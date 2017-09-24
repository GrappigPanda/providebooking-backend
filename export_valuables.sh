#!/usr/bin/fish

set -gx GUNICORN_WORKERS 3
set -gx GUNICORN_TIMEOUT 120
set -gx GUNICORN_LOG_LEVEL "debug"
set -gx KRONIKL_JWT_KEY "testsecretkey"
set -gx KRONIKL_JWT_EXPIRATION 15
set -gx KRONIKL_BRAINTREE_ENVIRONMENT "sandbox"
set -gx KRONIKL_BRAINTREE_MERCHANT_ID "sgppp5zt6vjkd3nx"
set -gx KRONIKL_BRAINTREE_PUBLIC_KEY "jbbsgnnp7dfk3yt7"
set -gx KRONIKL_BRAINTREE_PRIVATE_KEY "d8a1a6ce8de596691be3d0d18678d095"
set -gx KRONIKL_POSTGRES_FQDN "postgres://ian:ian@localhost/ian"
set -gx KRONIKL_EMAIL_FORWARD_TO "ian@ianleeclark.com"


