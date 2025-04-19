# The Back end for Shoppingify Webite

## Contributors
- Allani Ahmed <allania7med11@gmail.com>

---
## License & copyright
© Allani Ahmed, Full Stack Web Developer

## Project Links
- **Front End Repository**: [https://github.com/allania7med11/shop_front/](https://github.com/allania7med11/shop_front/)
- **Deployment**: [https://shop.effectivewebapp.com/](https://shop.effectivewebapp.com/)

## Environment Configuration

This section provides information about the environment configuration for this project.

### Environment Variables

This project uses a `.env` file to configure its environment. You can create a `.env` file in the project root directory, and set the following environment variables:

- `ENVIRONMENT`: Specifies the current environment (e.g., 'debug', 'dev', 'prod').
- `MIGRATE`: Controls whether The container will run migrate upon instantiation.
- `COLLECTSTATIC`: Controls whether The container will generate a static folder upon instantiation.
- `RUN_SCRIPTS`: Controls whether additional scripts will be executed upon container instantiation.
- `PORT`: Defines the port on which the application will listen.
- `DJANGO_DEBUG`: Controls whether Django should run in debug mode (true/false).
- `DJANGO_CORS_ALLOW_ALL_ORIGINS`: Allows cross-origin requests for development (true/false).
- `DJANGO_SECRET_KEY`: Django application's secret key for security. Please keep this confidential.
- `DJANGO_ALLOWED_HOSTS`: Configures allowed hosts for the Django application (comma-separated).
- `DJANGO_CSRF_TRUSTED_ORIGINS`: List of trusted origins for CSRF protection (comma-separated).
- `DJANGO_CORS_ALLOW_CREDENTIALS`: Specifies whether to allow credentials for cross-origin requests (true/false).
- `DJANGO_DEFAULT_FROM_EMAIL`: Default email address used in the From: header of outgoing emails. This address can take any format valid in the chosen email sending protocol.
- `POSTGRES_NAME`: The name of the PostgreSQL database for the application.
- `POSTGRES_USER`: The PostgreSQL database user.
- `POSTGRES_PASSWORD`: The password for the PostgreSQL user.
- `POSTGRES_HOST`: The hostname or IP address where the PostgreSQL database is hosted.
- `CLOUDINARY_NAME`: The name of the Cloudinary cloud where media files will be stored.
- `CLOUDINARY_API_KEY`: API key for Cloudinary.
- `CLOUDINARY_API_SECRET`: API secret for Cloudinary.
- `EMAIL_HOST_USER`: Your email address.
- `EMAIL_HOST_PASSWORD`: Your Google App password. You need to enable 2-Step Verification on your Google account and create an App password. Use this generated app password here.
- `STRIPE_PUBLISHABLE_KEY`: Your Stripe publishable key used for client-side requests.
- `STRIPE_SECRET_KEY`: Your Stripe secret key used for server-side requests.
- `SENTRY_DSN`: Your Sentry Data Source Name used for error tracking and monitoring in your application.
- `REDIS_URL`: The connection URL for Redis, used as a caching layer and message broker in your application.
- `OPENAI_API_KEY`: Your OpenAI API key used to authenticate requests to OpenAI's language models for AI-powered responses. 

Make sure to update these values to match your specific environment configuration. You can check .env.example for reference.

## Running the Project

To run the shop project follow these steps in https://github.com/allania7med11/shop