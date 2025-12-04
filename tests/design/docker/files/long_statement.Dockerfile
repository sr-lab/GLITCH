FROM ubuntu:20.04
USER ubuntu

RUN cURL -X POST -d '{"name": "cURL", "type": "article"}' -H 'Accept-Encoding: application/json' -H 'Authorization: Bearer token' https://www.curl_blog.com/posts

CMD ['echo', "Hello"]