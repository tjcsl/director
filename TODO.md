1. Use supervisor API instead of using `subprocess.Popen`
2. Create task queue using `celery` for tasks to do with `supervisor`, `nginx`, or creating directories/users on the filesystem
3. Implement usage of `Host` objects to proxy via `nginx`
4. `Process` should be distributed to a random `Host`
5. Drop users onto random `Host` for terminal
6. Distribute filesystem operations through `Host` objects
7. Drop users onto random `Host` for web editor
8. Try to implement real-time updates in web editor (not sure about this tbh)
