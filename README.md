# To run this on Heroku:

1. cd in to your local git repo directory.
2. Set environment vars on heroku:
    heroku config:set CAMPSITE_CLASS_NAME=<value> FROM_EMAIL=<value> FROM_EMAIL_PASSWORD=<value> TO_EMAIL=<value>
3. Push the app to heroku:
    git push heroku master
4. To start the app on heroku:
    heroku ps:scale worker=1
5. To view logs of script:
    heroku logs --tail