#!/bin/bash

set -e

echo "Wordpress Install Script"
echo

if [ -n "$SITE_NAME" ] || [ -n "$SITE_PURPOSE" ];
then
    echo "Installing for $SITE_PURPOSE site $SITE_NAME..."
else
    echo "No environment variables set!"
    echo "Are you running this script inside of the Director editor?"
    exit 1
fi

if [ $SITE_PURPOSE != "user" ] && [ $SITE_PURPOSE != "activity" ] && [ $SITE_PURPOSE != "project" ];
then
    echo "Please enter the URL of the website without a trailing slash."
    echo "For example, you should put 'https://example.com' if your website is located at example.com."
    echo "Enter the URL below:"
    read SITE_URL
fi

if [ "$SITE_PURPOSE" == "activity" ];
then
    SITE_URL="https://activities.tjhsst.edu/$SITE_NAME"
fi

if [ "$SITE_PURPOSE" == "user" ];
then
    SITE_URL="https://user.tjhsst.edu/$SITE_NAME"
fi

if [ ! -n "$SITE_URL" ];
then
    echo "Not setting an absolute site url..."
fi

cd $SITE_ROOT

if [ -d "public" ];
then
    if [ "$(ls -A public)"  ];
    then
        if [ ! -f "public/wp-config.php" ];
        then
            LOC="public_old_$(date +%s)"
            echo "The public folder is not empty, moving to $LOC..."
            mv public $LOC
        else
            echo "Existing Wordpress install detected."
            read -e -p "Do you want to overwrite the existing installation? [y/N] " choice
            if [[ "$choice" == [Yy]* ]];
            then
                rm -r public
            else
                echo "Aborting installation..."
                exit 1
            fi
        fi
    else
        rm -r public
    fi
fi

echo "Downloading Wordpress..."
echo

wget https://wordpress.org/latest.zip
unzip latest.zip
rm latest.zip

mv wordpress public

echo
echo
echo "Writing configuration files..."

cat > public/wp-config.php << EOL
<?php
\$db_opts = parse_url(getenv("DATABASE_URL"));
define('DB_NAME', ltrim(\$db_opts["path"], "/"));
define('DB_USER', \$db_opts["user"]);
define('DB_PASSWORD', \$db_opts["pass"]);
define('DB_HOST', \$db_opts["host"]);
define('DB_CHARSET', 'utf8');
define('DB_COLLATE', '');

EOL

echo
echo "Generating secret keys..."
echo

curl "https://api.wordpress.org/secret-key/1.1/salt/" >> public/wp-config.php

if [ -n "$SITE_URL" ];
then
echo
echo "Setting absolute urls..."

cat >> public/wp-config.php << EOL

define('WP_HOME', '$SITE_URL');
define('WP_SITEURL', '$SITE_URL');
EOL
fi

cat >> public/wp-config.php << EOL

\$table_prefix  = 'wp_';

define('WP_DEBUG', false);

if ( !defined('ABSPATH') )
    define('ABSPATH', dirname(__FILE__) . '/');

require_once(ABSPATH . 'wp-settings.php');
EOL

echo
echo "Wordpress installation finished!"
echo "1) You should press the 'Reset Permissions' button on the site page."
echo "   This ensures that Wordpress will be able to correctly apply updates."
echo
echo "2) Proceed to $SITE_URL to finish the Wordpress installation process."

sleep 1
