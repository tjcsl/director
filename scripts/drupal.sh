#!/bin/bash

set -e

echo "Drupal Install Script"
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
    echo "For example, you should put 'https://google.com' if your website is located at google.com."
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
        if [ ! -f "public/core/globals.api.php" ];
        then
            LOC="public_old_$(date +%s)"
            echo "The public folder is not empty, moving to $LOC..."
            mv public $LOC
        else
            echo "Existing Drupal install detected."
            read -e -p "Do you want to overwrite the existing installation? [y/N] " choice
            if [[ "$choice" == [Yy]* ]];
            then
                rm -rf public
            else
                echo "Aborting installation..."
                exit 1
            fi
        fi
    else
        rm -rf public
    fi
fi

echo "Downloading Drupal..."
echo

VER="8.3.7"

wget https://ftp.drupal.org/files/projects/drupal-$VER.tar.gz
tar -xvf drupal-$VER.tar.gz
rm drupal-$VER.tar.gz

mv drupal-$VER public

echo
echo
echo "Writing configuration files..."

echo
echo "Drupal installation finished!"
echo "1) You should press the 'Reset Permissions' button on the site page."
echo "   This ensures that Drupal will be able to correctly apply updates."
echo
echo "2) Proceed to $SITE_URL to finish the Drupal installation process."

sleep 3
