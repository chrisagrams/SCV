FROM nginx:1.21.6
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY ./static /www/data
COPY ./vendor /www/vendor