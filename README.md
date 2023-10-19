# The Back end for Shoppingify Webite

## Contributors
- Allani Ahmed <allania7med11@gmail.com>

---
## License & copyright
© Allani Ahmed, Full Stack Web Developer

## Front end Link
https://github.com/allania7med11/shop_front/

## Deployment Link
https://shop.effectivewebapp.com/

## Environment Configuration

This section provides information about the environment configuration for this project.

### Environment Variables

This project uses a `.env` file to configure its environment. You can create a `.env` file in the project root directory, and set the following environment variables:

- `ENVIRONMENT`: Specifies the current environment (e.g., 'debug', 'dev', 'prod').
- `PORT`: Defines the port on which the application will listen.
- `DJANGO_DEBUG`: Controls whether Django should run in debug mode (True/False).
- `DJANGO_CORS_ALLOW_ALL_ORIGINS`: Allows cross-origin requests for development (True/False).
- `DJANGO_SECRET_KEY`: Django application's secret key for security. Please keep this confidential.
- `DJANGO_ALLOWED_HOSTS`: Configures allowed hosts for the Django application.
- `POSTGRES_NAME`: The name of the PostgreSQL database for the application.
- `POSTGRES_USER`: The PostgreSQL database user.
- `POSTGRES_PASSWORD`: The password for the PostgreSQL user.
- `POSTGRES_HOST`: The hostname or IP address where the PostgreSQL database is hosted.
- `CLOUDINARY_NAME`: The name of the Cloudinary cloud where media files will be stored.
- `CLOUDINARY_API_KEY`: API key for Cloudinary.
- `CLOUDINARY_API_SECRET`: API secret for Cloudinary.
- `UID`: User ID (User identifier).
- `GID`: Group ID (Group identifier).

Please ensure that sensitive information like `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD`, `CLOUDINARY_API_KEY`, and `CLOUDINARY_API_SECRET` is kept secure and not shared in public repositories or with unauthorized users.

Make sure to update these values to match your specific environment configuration, and consider maintaining a separate `.env.example` file with placeholders for these values for security purposes.