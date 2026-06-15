import pytest
try:
    import cPickle as pickle
except ImportError:
    import pickle

from .models import Post


pytestmark = pytest.mark.django_db


@pytest.fixture
def post():
    return Post.objects.create(title='Pickling')


def test_equal(post):
    restored = pickle.loads(pickle.dumps(post, -1))
    assert restored == post


def test_packed(post):
    stored = pickle.dumps(post)
    assert b'model_unpickle' in stored  # Our unpickling function is used
    assert b'title' not in stored       # Attributes are packed


def test_state_packed(post):
    stored = pickle.dumps(post, -1)
    assert b'_state' not in stored
    assert b'db' not in stored
    assert b'adding' not in stored


def test_deferred(post):
    p = Post.objects.defer('title').get(pk=post.pk)
    restored = pickle.loads(pickle.dumps(p, -1))
    assert restored == p


def test_field_swap(post):
    stored = pickle.dumps(post, -1)
    Post._meta.fields = Post._meta.fields[::-1]
    # Drop attnames cache
    from django_pickling import attnames
    attnames.__defaults__[0].pop(Post)

    assert pickle.loads(stored) == post


def test_reload():
    import importlib
    from django.db.models import Model
    import django_pickling
    
    # 1. Reload when already patched (triggers False condition on monkeypatch check)
    importlib.reload(django_pickling)
    
    # 2. Reload when not patched, with __setstate__ (triggers True condition and deletes __setstate__)
    orig = Model.__reduce__
    try:
        def dummy_reduce(self):
            pass
        Model.__reduce__ = dummy_reduce
        Model.__setstate__ = lambda self, state: None
        
        importlib.reload(django_pickling)
        
        assert Model.__reduce__.__name__ == 'Model__reduce__'
        assert not hasattr(Model, '__setstate__')
    finally:
        Model.__reduce__ = orig

    # 3. Reload when not patched, without __setstate__ (triggers True condition, but skips deleting __setstate__)
    try:
        def dummy_reduce(self):
            pass
        Model.__reduce__ = dummy_reduce
        if hasattr(Model, '__setstate__'):
            del Model.__setstate__
            
        importlib.reload(django_pickling)
        
        assert Model.__reduce__.__name__ == 'Model__reduce__'
    finally:
        Model.__reduce__ = orig





def test_apps_not_ready(post):
    from unittest.mock import patch
    from django.apps import apps
    from django_pickling import model_unpickle

    # Clear cache to force cache miss
    model = 'tests.Post'
    model_unpickle.__defaults__[0].pop(model, None)

    with patch.object(apps, 'ready', False):
        with patch.object(apps, 'populate') as mock_populate:
            restored = pickle.loads(pickle.dumps(post, -1))
            assert restored == post
            assert mock_populate.called

