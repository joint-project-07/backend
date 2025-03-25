docker-compose run --rm --entrypoint "\
  certbot certonly \
  -d dietstory.shop \
  -d *.dietstory.shop \
  --email thfqlsla35@gmail.com \
  --manual --preferred-challenges dns \
  --server https://acme-v02.api.letsencrypt.org/directory \
  --force-renewal" certbot

docker-compose exec nginx nginx -s reload