import os
import io
import shutil
import stat
import zipfile
import mimetypes

from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods

from ..models import Site, Process
from ..helpers import (fix_permissions, create_process_config, reload_php_fpm,
                       render_to_string, check_nginx_config, reload_nginx_config,
                       create_config_files, update_supervisor,
                       add_access_token)
from ..database_helpers import get_sql_version

from raven.contrib.django.raven_compat.models import client


@login_required
@add_access_token
def editor_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    context = {
        "site": site,
        "raven_dsn": client.get_public_dsn(),
        "sql_version": get_sql_version(site) if hasattr(site, "database") else None
    }

    return render(request, "sites/editor.html", context)


@login_required
def editor_path_view(request, site_id):
    """Returns a list of files and folders in the requested path."""
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    requested_path = request.GET.get("path", "")
    path = os.path.abspath(os.path.join(site.path, requested_path))

    if not path.startswith(site.path) or not os.path.isdir(path):
        return JsonResponse({"error": "Invalid or nonexistent path!", "path": path})

    filesystem = []

    for f in os.listdir(path):
        fpath = os.path.join(path, f)
        fmode = os.lstat(fpath).st_mode
        if stat.S_ISDIR(fmode):
            obj = {"type": "d", "name": f}
        else:
            obj = {"type": "f", "name": f, "executable": fmode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)}
        if stat.S_ISLNK(fmode):
            obj["link"] = True
        filesystem.append(obj)

    return JsonResponse({"files": sorted(filesystem, key=lambda x: (x["type"], x["name"][0] == ".", x["name"]))})


@login_required
def editor_load_view(request, site_id):
    """Reads the requested file and returns it to the client."""
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    requested_path = request.GET.get("name", "")
    path = os.path.abspath(os.path.join(site.path, requested_path))

    if not path.startswith(site.path) or not os.path.isfile(path):
        return JsonResponse({"error": "Invalid or nonexistent file!", "path": path})

    try:
        with open(path, "r") as f:
            contents = f.read()
    except UnicodeDecodeError:
        return JsonResponse({"error": "Editing binary files is not supported!"})
    except IOError:
        return JsonResponse({"error": "Failed to open file!"})

    return JsonResponse({"contents": contents})


@login_required
def editor_save_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    requested_path = request.GET.get("name", "")
    path = os.path.abspath(os.path.join(site.path, requested_path))

    if not path.startswith(site.path):
        return JsonResponse({"error": "Invalid or nonexistent file!", "path": path})

    set_perms = False

    if not os.path.isfile(path):
        if os.path.exists(path):
            return JsonResponse({"error": "Invalid or nonexistent file!", "path": path})
        if not request.POST.get("force", False):
            return JsonResponse({"error": "The file you are editing does not exist anymore!", "path": path, "force": True})
        else:
            set_perms = True

    with open(path, "w") as f:
        f.write(request.POST.get("contents"))

    if set_perms:
        st = os.lstat(path)
        os.lchown(path, site.user.id, site.group.id)
        os.chmod(path, st.st_mode | stat.S_IRGRP | stat.S_IWGRP)

    return JsonResponse({"success": True})


@require_http_methods(["POST"])
@login_required
def editor_delete_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    requested_path = request.POST.getlist("name[]")
    path = [os.path.abspath(os.path.join(site.path, x)) for x in requested_path]

    if not all(x.startswith(site.path) for x in path) or not all(os.path.exists(x) for x in path):
        return JsonResponse({"error": "Invalid or nonexistent file or folder!", "path": path})

    for p in path:
        try:
            if os.path.isfile(p):
                os.remove(p)
            else:
                shutil.rmtree(p)
        except FileNotFoundError:
            # File might have been deleted after the check
            pass

    return JsonResponse({"success": True})


@require_http_methods(["POST"])
@login_required
def editor_create_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    is_file = request.POST.get("type", "f") == "f"

    requested_path = request.POST.get("path", "")
    requested_new = os.path.basename(request.POST.get("name", ""))
    path = os.path.abspath(os.path.join(site.path, requested_path))

    if not path.startswith(site.path) or not os.path.isdir(path):
        return JsonResponse({"error": "Invalid or nonexistent folder!", "path": path})

    new_path = os.path.join(path, requested_new)

    if os.path.exists(new_path):
        return JsonResponse({"error": "The file or folder you are trying to create already exists!"})

    if is_file:
        open(new_path, "a").close()
    else:
        os.mkdir(new_path)

    os.lchown(new_path, site.user.id, site.group.id)

    return JsonResponse({"success": True})


@login_required
def editor_download_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    requested_path = request.GET.get("name", "")
    path = os.path.abspath(os.path.join(site.path, requested_path))

    if not path.startswith(site.path) or not os.path.exists(path):
        raise Http404

    if os.path.isfile(path):
        response = HttpResponse(content=open(path, "rb"))
        if request.GET.get("embed", False) is not False:
            response["Content-Type"] = mimetypes.guess_type(path)[0]
        else:
            response["Content-Type"] = "application/octet-stream"
            response["Content-Disposition"] = "attachment; filename={}".format(os.path.basename(path))
        return response
    else:
        zip_io = io.BytesIO()
        with zipfile.ZipFile(zip_io, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(path):
                for f in files:
                    filepath = os.path.join(root, f)
                    zipf.write(filepath, filepath[len(path):])
        response = HttpResponse(zip_io.getvalue())
        response["Content-Type"] = "application/x-zip-compressed"
        response["Content-Disposition"] = "attachment; filename={}.zip".format(os.path.basename(path))
        response["Content-Length"] = zip_io.tell()
        return response


@require_http_methods(["POST"])
@login_required
def editor_rename_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    new_name = os.path.basename(request.POST.get("newname", ""))
    requested_path = request.POST.get("name", "")
    path = os.path.abspath(os.path.join(site.path, requested_path))

    if not requested_path:
        return JsonResponse({"error": "You cannot rename the root directory!"})

    if not path.startswith(site.path) or not os.path.exists(path):
        return JsonResponse({"error": "Invalid or nonexistent file or folder!", "path": path})

    if not new_name:
        return JsonResponse({"error": "You must enter a valid name!", "path": path})

    os.rename(path, os.path.join(os.path.dirname(path), new_name))

    return JsonResponse({"success": True})


@require_http_methods(["POST"])
@login_required
def editor_upload_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    name = request.POST.get("path", "")
    path = os.path.abspath(os.path.join(site.path, name))

    if not path.startswith(site.path) or not os.path.isdir(path):
        return JsonResponse({"error": "Invalid or nonexistent folder!", "path": path})

    fs = request.FILES.getlist("file[]")

    if len(fs) == 0:
        return JsonResponse({"error": "No file(s) uploaded!"})

    for f in fs:
        filename = os.path.basename(f.name)
        with open(os.path.join(path, filename), "wb") as dest:
            for chunk in f.chunks():
                dest.write(chunk)

    fix_permissions(site)

    return JsonResponse({"success": True})


@require_http_methods(["POST"])
@login_required
def editor_move_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    old_path = request.POST.get("old", "")
    new_path = request.POST.get("new", "")
    old_path = os.path.abspath(os.path.join(site.path, old_path))
    new_path = os.path.abspath(os.path.join(site.path, new_path))
    new_file = os.path.join(new_path, os.path.basename(old_path))

    if not old_path.startswith(site.path) or not os.path.exists(old_path):
        return JsonResponse({"error": "Invalid or nonexistent file or folder!", "path": old_path})

    if not new_path.startswith(site.path):
        return JsonResponse({"error": "Invalid destination!", "path": new_path})

    if os.path.exists(new_file):
        return JsonResponse({"error": "The destination you are trying to copy to already exists.", "path": new_file})

    if new_file.startswith(os.path.join(old_path, "")):
        return JsonResponse({"error": "You cannot place a folder inside itself!"})

    os.rename(old_path, new_file)

    return JsonResponse({"success": True})


@require_http_methods(["POST"])
@login_required
def editor_process_view(request, site_id):
    """Set the server process script file for dynamic sites."""
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    path = request.POST.get("name", None)

    if not path:
        return JsonResponse({"error": "No file path received!"})

    path = os.path.abspath(os.path.join(site.path, path))

    if not path.startswith(site.path) or not os.path.isfile(path):
        return JsonResponse({"error": "Invalid or nonexistent file!"})

    if not os.access(path, os.X_OK):
        return JsonResponse({"error": "File not set as executable!"})

    if Process.objects.filter(site=site).exists():
        proc = Process.objects.get(site=site)
        proc.path = path
        proc.save()
    else:
        proc = Process.objects.create(site=site, path=path)

    create_process_config(proc)
    update_supervisor()

    return JsonResponse({"success": True})


@require_http_methods(["POST"])
@login_required
def editor_exec_view(request, site_id):
    """Set/unset the executable bit for the requested files."""
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    paths = request.POST.getlist("name[]", [])
    on = request.POST.get("on", False) == "true"

    if request.POST.get("name", False):
        paths.append(request.POST.get("name"))

    if not paths:
        return JsonResponse({"error": "No file path received!"})

    paths = [os.path.abspath(os.path.join(site.path, x)) for x in paths]

    for path in paths:
        if not path.startswith(site.path) or not os.path.isfile(path):
            return JsonResponse({"error": "Invalid or nonexistent file!"})

    for path in paths:
        st = os.stat(path)
        if on:
            os.chmod(path, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        else:
            os.chmod(path, stat.S_IMODE(st.st_mode) & ~stat.S_IXUSR & ~stat.S_IXGRP & ~stat.S_IXOTH)

    return JsonResponse({"success": True})


@login_required
def edit_nginx_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    nginx_path = "/etc/nginx/director.d/{}.conf".format(site.name)

    if os.path.isfile(nginx_path):
        with open(nginx_path, "r") as f:
            contents = f.read()
    else:
        contents = render_to_string("config/nginx.conf", {"site": site})

    if request.method == "POST":
        if not request.user.is_superuser:
            return JsonResponse({"error": "You are not allowed to make changes to this file!"})
        if not site.custom_nginx:
            if request.POST.get("force", False):
                site.custom_nginx = True
                site.save()
            else:
                return JsonResponse({"error": "You must enable custom nginx configuration before editing this file.", "force": True})
        if request.POST.get("editor", None):
            with open(nginx_path, "w") as f:
                f.write(request.POST["editor"])
            if not check_nginx_config():
                with open(nginx_path, "w") as f:
                    f.write(contents)
                return JsonResponse({"error": "Invalid nginx configuration!"})
            else:
                reload_nginx_config()
                return JsonResponse({"success": "Nginx configuration updated!"})
        else:
            return JsonResponse({"error": "You must have a nginx configuration!"})
    else:
        return HttpResponse(contents, content_type="text/plain")


@login_required
@add_access_token
def web_terminal_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    context = {
        "site": site
    }

    return render(request, "sites/web_terminal.html", context)


@require_http_methods(["POST"])
@login_required
def site_type_view(request, site_id):
    """Change the site category between static, PHP, and dynamic."""
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    if request.POST.get("type") not in ["static", "php", "dynamic"]:
        return JsonResponse({"error": "Invalid site type!"})

    site.category = request.POST.get("type")
    site.save()

    create_config_files(site)
    if site.category != "dynamic" and hasattr(site, "process"):
        site.process.delete()

    if site.category == "php":
        reload_php_fpm()

    reload_nginx_config()

    return JsonResponse({"success": True})
