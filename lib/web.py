from requests import Session
from safetywrap import Result

def get_ok(sess: Session, url):
    response = sess.get(url)
    response.raise_for_status()
    return response

def try_get(sess: Session, url):
    return Result.of(get_ok, sess, url)
