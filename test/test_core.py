# -*- coding: utf-8 -*-

# python std lib
import logging

# djinja package imports
import djinja
from djinja.main import Core
from djinja.conftree import ConfTree

# 3rd party imports
import pytest
from jinja2 import Template
from testfixtures import LogCapture


def test_create_obj():
    """
    Create empty object and ensure defaults is set correctly
    """
    c = Core({})
    assert c.args == {}

    # Test that loading all default config files works
    ct = ConfTree()
    assert ct.tree == c.config.get_tree()


def test_parse_env_vars():
    """
    Test setting env variables from cli and ensure they are set
    correctly in configuration.
    """
    c = Core({
        "--env": [
            "foo=bar",
            "opa=1",
            "barfoo=True",
        ]
    })

    c.parse_env_vars()
    assert c.config.get("foo") == "bar"
    assert c.config.get("opa") == "1"
    assert c.config.get("barfoo") == "True"


def test_parse_env_vars_invalid_key():
    """
    Test that invalid keyformats cause exceptions
    """
    # specify a key that do not follow the key=value structures
    c = Core({
        "--env": [
            "foo:bar"
        ]
    })
    with pytest.raises(Exception) as ex:
        c.parse_env_vars()
    # TODO: str() maybe not py2 & 3 compatible. Look into unicode in from redis._compat
    assert str(ex.value).startswith("var 'foo:bar' is not of format 'key=value'")

    c = Core({
        "--env": [
            "foo="
        ]
    })
    with pytest.raises(Exception) as ex:
        c.parse_env_vars()
    # TODO: str() maybe not py2 & 3 compatible. Look into unicode in from redis._compat
    assert str(ex.value).startswith("var 'foo=' is not of format 'key=value'")

    c = Core({
        "--env": [
            "=bar"
        ]
    })
    with pytest.raises(Exception) as ex:
        c.parse_env_vars()
    # TODO: str() maybe not py2 & 3 compatible. Look into unicode in from redis._compat
    assert str(ex.value).startswith("var '=bar' is not of format 'key=value'")


def test_parse_no_env_vars():
    """
    Test that if no env variables is specefied none should be loaded
    """
    c = Core({})
    c.parse_env_vars()
    assert c.config.get_tree().get("env", {}) == {}


def test_load_user_specefied_config_files(tmpdir):
    """
    Test that loadinloading of config files that user specefies work
    and that config keys is set correctly.
    """
    f1 = tmpdir.join("foo.json")
    f2 = tmpdir.join("foo.yaml")
    f1.write('{"foo": "bar"}')
    f2.write('foo: foo')

    c = Core({
        "--config": [str(f1), str(f2)]
    })
    c.load_user_specefied_config_files()
    assert c.config.get_tree() == {"foo": "foo"}


def test_load_no_user_specefied_config_files():
    """
    Test that user specified
    """
    c = Core({
        "--config": ["/tmp/foobar/opalopa"]
    })
    with pytest.raises(SystemExit) as ex:
        c.load_user_specefied_config_files()
    assert ex.value.message == "config not loaded"


def test_load_user_specefied_config_file_wrong_format(tmpdir):
    """
    Config data is a dict at top level and loading something else should raise error
    """
    f = tmpdir.join("empty.json")
    f.write('{"foo", "bar]')
    c = Core({
        "--config": [str(f)]
    })
    with pytest.raises(SystemExit) as ex:
        c.load_user_specefied_config_files()
    assert ex.value.message == "config not loaded"


def test_handle_datasources(tmpdir):
    """
    Test that loading of datasources work and that they are usable.
    """

    sample_data = """
def _filter_upper(string):
    return string.upper()

def _global_lower(string):
    return string.lower()
    """
    inp = tmpdir.join("Dockerfile.jinja")
    inp.write("{{ 'foo'|upper }} : {{ lower('BAR') }}")

    out = tmpdir.join("Dockerfile")
    dsfile = tmpdir.join("_datasource.py")
    dsfile.write(sample_data)

    c = Core({
        "--dockerfile": str(inp),
        "--outfile": str(out),
        "--datasource": [str(dsfile)]
    })
    c.main()
    assert out.read() == "FOO : bar"


def test_fail_load_non_existing_datasource(tmpdir):
    """
    Prove a path to a datasource that do not exists and try to load it
    and look for exception to be raised.
    """
    inp = tmpdir.join("Dockerfile.jinja")
    out = tmpdir.join("Dockerfile")
    c = Core({
        "--dockerfile": str(inp),
        "--outfile": str(out),
        "--datasource": ["/tmp/foobar/barfoo"]
    })
    with pytest.raises(SystemExit) as ex:
        c.main()
    assert ex.value.message == "import failed"


def test_load_datasource_import_error(tmpdir):
    """
    Provide a datasource file that will raise ImportError. Ensure log msg
    and that exception was raised.

    We fake the ImportError exception by manually raising it from inside
    the datasource file to make it consistent.
    """
    inp = tmpdir.join("Dockerfile.jinja")
    inp.write("foobar")
    out = tmpdir.join("Dockerfile")
    dsfile = tmpdir.join("_datasource_.py")
    dsfile.write("""
raise ImportError("foobar")
    """)
    c = Core({
        "--dockerfile": str(inp),
        "--outfile": str(out),
        "--datasource": [str(dsfile)]
    })
    with pytest.raises(SystemExit) as ex:
        c.main()
    assert ex.value.message == "import failed"


def test_process_dockerfile(tmpdir):
    """
    Test dockerfile processed, substitute data from config.
    """
    inp = tmpdir.join("Dockerfile.jinja")
    inp.write("{{ barfoo }}")
    out = tmpdir.join("Dockerfile")
    c = tmpdir.join("conf.json")
    c.write('{"barfoo": "foobar"}')

    c = Core({
        "--dockerfile": str(inp),
        "--outfile": str(out),
        "--config": [str(c)],
    })

    c.main()
    assert out.read() == "foobar"


def test_attach_function():
    """
    Test that it works to attach a function to the global namespace that
    jinja will later use.
    """
    c = Core({})

    def foo_func():
        pass
    c.attach_function("globals", foo_func, "func")

    assert "func" in c.environment_vars["globals"]
    assert c.environment_vars["globals"]["func"] == foo_func

    # Test that exception is raised if we try to attach to wrong jinja namespace
    with pytest.raises(KeyError) as ex:
        c.attach_function("foobar", foo_func, "func")
    assert str(ex.value).startswith("'foobar'")

    # TODO: Test that if you attach the same function twice to the same namespace
    #       it should fail with some exception


def test_update_template_env(tmpdir):
    """
    """
    global _local_env

    i = tmpdir.join("Dockerfile.jinja")
    i.write("{{ func() }}")
    o = tmpdir.join("Dockerfile")

    c = Core({
        "--dockerfile": str(i),
        "--outfile": str(o),
    })

    def foo_func():
        return "foobar"
    c.attach_function("globals", foo_func, "func")

    template = Template(i.read())
    c.update_template_env(template.environment)
    rendered_template = template.render()
    assert rendered_template == "foobar"


def test_main(tmpdir):
    test_process_dockerfile(tmpdir)


def test_debug_logging():
    """
    Test that if -vvvvv is passed into docopt and debug logging will output.
    """

    djinja.init_logging(5)
    Log = logging.getLogger("foobar")
    with LogCapture() as l:
        Log.debug("barfoo")
        l.check(("foobar", "DEBUG", "barfoo"))
