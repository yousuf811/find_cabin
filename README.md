# To run this on Heroku:

1. cd in to your local git repo directory.
2. Set environment vars on heroku:
    heroku config:set FROM_EMAIL=<value> FROM_EMAIL_PASSWORD=<value> STEEP_RAVINE_INFO=<value> BLACK_MOUNTAIN_INFO=<value> ADMIN_EMAIL=<email>
See .env (not checked in github) for exact values.
3. Push the app to heroku:
    git push heroku master
4. To start the app on heroku:
    heroku ps:scale find_cabin=1
5. To view logs of script:
    heroku logs --tail