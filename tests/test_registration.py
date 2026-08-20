import contextlib
import importlib.metadata
import json
import multiprocessing
import os
import shutil
import socket
import subprocess
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest import mock

HERMES_COMMIT = "f80f453ae0679347e38abc917c7f94f717bf96c5"
HERMES_PACKAGE_VERSION = "0.20.1"


def _update_selection(home, ready, start, arguments):
    os.environ["HERMES_HOME"] = home
    from hermes_prompt_controls import _command

    ready.put(True)
    start.wait()
    if _command(arguments) != "Selection updated.":
        raise RuntimeError("fictional selection update failed")


class PluginRegistrationTest(unittest.TestCase):
    def test_config_updates_from_two_processes_preserve_both_selections(self):
        context = multiprocessing.get_context("spawn")
        with tempfile.TemporaryDirectory() as temporary_directory:
            hermes_home = Path(temporary_directory)
            plugin_home = hermes_home / "prompt-controls"
            directives = plugin_home / "directives"
            directives.mkdir(parents=True)
            (directives / "platform.md").write_text("Platform", encoding="utf-8")
            (directives / "model.md").write_text("Model", encoding="utf-8")
            config_path = plugin_home / "config.json"
            config_path.write_text(
                json.dumps({"global": [], "platforms": {}, "models": {}}),
                encoding="utf-8",
            )

            ready = context.Queue()
            start = context.Event()
            processes = (
                context.Process(
                    target=_update_selection,
                    args=(
                        str(hermes_home),
                        ready,
                        start,
                        "set platform telegram platform.md",
                    ),
                ),
                context.Process(
                    target=_update_selection,
                    args=(
                        str(hermes_home),
                        ready,
                        start,
                        "set model fictional-model model.md",
                    ),
                ),
            )
            for process in processes:
                process.start()
            ready.get(timeout=10)
            ready.get(timeout=10)
            start.set()
            for process in processes:
                process.join(timeout=10)
                self.assertEqual(process.exitcode, 0)

            self.assertEqual(
                json.loads(config_path.read_text(encoding="utf-8")),
                {
                    "global": [],
                    "platforms": {"telegram": ["platform.md"]},
                    "models": {"fictional-model": ["model.md"]},
                },
            )

    def test_entry_point_rewrites_fictional_system_requests_without_network(self):
        git = shutil.which("git")
        self.assertIsNotNone(git, "git is required to verify the Hermes baseline")

        entry_points = importlib.metadata.entry_points().select(
            group="hermes_agent.plugins", name="prompt-controls"
        )
        self.assertEqual(
            [entry_point.value for entry_point in entry_points],
            ["hermes_prompt_controls"],
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            hermes_home = root / "home"
            plugin_home = hermes_home / "prompt-controls"
            directives = plugin_home / "directives"
            bundled_plugins = root / "bundled"
            directives.mkdir(parents=True)
            bundled_plugins.mkdir()
            (hermes_home / "config.yaml").write_text(
                "plugins:\n  enabled:\n    - prompt-controls\n",
                encoding="utf-8",
            )

            directive_contents = {
                "global.md": "Fictional global directive",
                "telegram.md": "Fictional Telegram directive",
                "model.md": "Fictional model directive",
                "session.md": "Fictional session directive",
            }
            for name, content in directive_contents.items():
                (directives / name).write_text(content, encoding="utf-8")

            config_path = plugin_home / "config.json"
            session_state_path = plugin_home / "session-state.json"

            def write_json(path, value):
                path.write_text(json.dumps(value), encoding="utf-8")

            write_json(
                config_path,
                {
                    "global": ["global.md"],
                    "platforms": {"telegram": ["telegram.md"]},
                    "models": {"fictional-model": ["global.md", "model.md"]},
                },
            )
            write_json(
                session_state_path,
                {"sessions": {"fictional-session": ["session.md"]}},
            )

            environment = {
                "HERMES_HOME": str(hermes_home),
                "HERMES_BUNDLED_PLUGINS": str(bundled_plugins),
                "HOME": str(root),
                "USERPROFILE": str(root),
            }
            for name in ("SYSTEMROOT", "WINDIR", "TEMP", "TMP"):
                if value := os.environ.get(name):
                    environment[name] = value

            with mock.patch.dict(os.environ, environment, clear=True):
                from hermes_cli import plugins as plugins_module
                from hermes_cli.middleware import apply_llm_request_middleware

                hermes_checkout = Path(plugins_module.__file__).resolve().parents[1]
                revision = subprocess.run(
                    [git, "-C", str(hermes_checkout), "rev-parse", "HEAD"],
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip()
                self.assertEqual(revision, HERMES_COMMIT)
                self.assertEqual(
                    importlib.metadata.version("hermes-agent"),
                    HERMES_PACKAGE_VERSION,
                )

                manager = plugins_module.PluginManager()
                try:
                    blocked_operation = AssertionError(
                        "plugin attempted network or process access"
                    )
                    with contextlib.ExitStack() as blocked:
                        for method in ("connect", "connect_ex", "sendto"):
                            blocked.enter_context(
                                mock.patch.object(
                                    socket.socket,
                                    method,
                                    side_effect=blocked_operation,
                                )
                            )
                        blocked.enter_context(
                            mock.patch(
                                "socket.create_connection",
                                side_effect=blocked_operation,
                            )
                        )
                        blocked.enter_context(
                            mock.patch(
                                "subprocess.Popen",
                                side_effect=blocked_operation,
                            )
                        )
                        manager.discover_and_load()

                        plugin = manager._plugins["prompt-controls"]
                        self.assertTrue(plugin.enabled, plugin.error)
                        self.assertEqual(plugin.middleware_registered, ["llm_request"])
                        self.assertEqual(
                            plugin.commands_registered, ["prompt-controls"]
                        )
                        self.assertEqual(
                            plugin.module.__name__,
                            "hermes_prompt_controls",
                        )

                        callback = manager._middleware["llm_request"][0]
                        callback_spy = mock.Mock(wraps=callback)
                        manager._middleware["llm_request"][0] = callback_spy

                        def apply(request, **context):
                            with mock.patch.object(
                                plugins_module,
                                "get_plugin_manager",
                                return_value=manager,
                            ):
                                return apply_llm_request_middleware(
                                    request,
                                    api_mode="chat_completions",
                                    platform="telegram",
                                    session_id="fictional-session",
                                    **context,
                                )

                        request = {
                            "model": "fictional-model",
                            "temperature": 0.2,
                            "prompt_cache_key": "fictional-cache-key",
                            "messages": [
                                {"role": "user", "content": "Fictional question"},
                                {
                                    "role": "system",
                                    "content": "Fictional baseline",
                                    "cache_control": {"type": "ephemeral"},
                                },
                            ],
                        }
                        original_request = deepcopy(request)
                        directive = "\n\n".join(directive_contents.values())
                        result = apply(request)

                        self.assertEqual(request, original_request)
                        self.assertEqual(result.original_payload, original_request)
                        self.assertIsNot(result.payload, request)
                        self.assertEqual(
                            result.payload["messages"],
                            [
                                {"role": "user", "content": "Fictional question"},
                                {
                                    "role": "system",
                                    "content": f"{directive}\n\nFictional baseline",
                                    "cache_control": {"type": "ephemeral"},
                                },
                            ],
                        )
                        self.assertEqual(result.payload["temperature"], 0.2)
                        self.assertEqual(
                            result.payload["prompt_cache_key"],
                            "fictional-cache-key",
                        )
                        self.assertTrue(result.changed)
                        self.assertEqual(result.trace, [{"source": "prompt-controls"}])

                        idempotent_result = apply(result.payload)
                        self.assertEqual(idempotent_result.payload, result.payload)
                        self.assertFalse(idempotent_result.changed)
                        self.assertEqual(idempotent_result.trace, [])

                        no_system_request = {
                            "model": "fictional-model",
                            "messages": [
                                {"role": "user", "content": "Fictional question"}
                            ],
                        }
                        no_system_original = deepcopy(no_system_request)
                        no_system_result = apply(no_system_request)
                        self.assertEqual(no_system_request, no_system_original)
                        self.assertEqual(
                            no_system_result.payload["messages"][0],
                            {"role": "system", "content": directive},
                        )

                        write_json(
                            config_path,
                            {"global": [], "platforms": {}, "models": {}},
                        )
                        write_json(session_state_path, {"sessions": {}})
                        warning_spy = mock.Mock()
                        with mock.patch.object(
                            plugin.module.logger,
                            "warning",
                            warning_spy,
                        ):
                            missing_mapping_result = apply(request)
                        self.assertEqual(missing_mapping_result.payload, request)
                        self.assertFalse(missing_mapping_result.changed)
                        warning_spy.assert_not_called()

                        private_value = "private-content"
                        private_path = "C:\\private\\directive.md"
                        invalid_configs = (
                            "{",
                            json.dumps({"unknown": [private_value, private_path]}),
                            json.dumps(
                                {
                                    "global": ["../private.md"],
                                    "platforms": {},
                                    "models": {},
                                }
                            ),
                            json.dumps(
                                {
                                    "global": ["missing.md"],
                                    "platforms": {},
                                    "models": {},
                                }
                            ),
                        )
                        for invalid_config in invalid_configs:
                            with self.subTest(invalid_config=invalid_config):
                                config_path.write_text(
                                    invalid_config,
                                    encoding="utf-8",
                                )
                                warning_spy.reset_mock()
                                with mock.patch.object(
                                    plugin.module.logger,
                                    "warning",
                                    warning_spy,
                                ):
                                    invalid_config_result = apply(request)
                                self.assertEqual(invalid_config_result.payload, request)
                                warning_spy.assert_called_once_with(
                                    "Prompt controls configuration is invalid; "
                                    "request left unchanged."
                                )
                                diagnostic = str(warning_spy.call_args)
                                self.assertNotIn(private_value, diagnostic)
                                self.assertNotIn(private_path, diagnostic)
                                self.assertNotIn(str(plugin_home), diagnostic)

                        outside_directive = root / "outside.md"
                        outside_directive.write_text(
                            "External content", encoding="utf-8"
                        )
                        linked_directive = directives / "linked.md"
                        try:
                            linked_directive.symlink_to(outside_directive)
                        except OSError:
                            pass
                        else:
                            write_json(
                                config_path,
                                {
                                    "global": ["linked.md"],
                                    "platforms": {},
                                    "models": {},
                                },
                            )
                            warning_spy.reset_mock()
                            with mock.patch.object(
                                plugin.module.logger,
                                "warning",
                                warning_spy,
                            ):
                                linked_file_result = apply(request)
                            self.assertEqual(linked_file_result.payload, request)
                            warning_spy.assert_called_once_with(
                                "Prompt controls configuration is invalid; "
                                "request left unchanged."
                            )
                            linked_directive.unlink()

                        external_directory = root / "external-directives"
                        external_directory.mkdir()
                        (external_directory / "external.md").write_text(
                            "External content",
                            encoding="utf-8",
                        )
                        saved_directives = plugin_home / "saved-directives"
                        directives.rename(saved_directives)
                        try:
                            try:
                                directives.symlink_to(
                                    external_directory,
                                    target_is_directory=True,
                                )
                            except OSError:
                                pass
                            else:
                                write_json(
                                    config_path,
                                    {
                                        "global": ["external.md"],
                                        "platforms": {},
                                        "models": {},
                                    },
                                )
                                warning_spy.reset_mock()
                                with mock.patch.object(
                                    plugin.module.logger,
                                    "warning",
                                    warning_spy,
                                ):
                                    linked_directory_result = apply(request)
                                self.assertEqual(
                                    linked_directory_result.payload, request
                                )
                                warning_spy.assert_called_once_with(
                                    "Prompt controls configuration is invalid; "
                                    "request left unchanged."
                                )
                        finally:
                            if directives.is_symlink():
                                directives.unlink()
                            saved_directives.rename(directives)

                        write_json(
                            config_path,
                            {"global": ["global.md"], "platforms": {}, "models": {}},
                        )
                        warning_spy.reset_mock()
                        with mock.patch.object(
                            plugin.module.logger,
                            "warning",
                            warning_spy,
                        ):
                            unsupported_shape_result = apply(
                                {"model": "fictional-model", "messages": "invalid"}
                            )
                        self.assertEqual(
                            unsupported_shape_result.payload,
                            {"model": "fictional-model", "messages": "invalid"},
                        )
                        warning_spy.assert_called_once_with(
                            "Prompt controls request shape is unsupported; "
                            "request left unchanged."
                        )

                        warning_spy.reset_mock()
                        with mock.patch.object(
                            plugin.module.logger,
                            "warning",
                            warning_spy,
                        ):
                            with mock.patch.object(
                                plugins_module,
                                "get_plugin_manager",
                                return_value=manager,
                            ):
                                unsupported_mode_result = apply_llm_request_middleware(
                                    request,
                                    api_mode="responses",
                                )
                        self.assertEqual(unsupported_mode_result.payload, request)
                        warning_spy.assert_called_once_with(
                            "Prompt controls request shape is unsupported; "
                            "request left unchanged."
                        )

                        write_json(
                            config_path,
                            {"global": [], "platforms": {}, "models": {}},
                        )
                        command = manager._plugin_commands["prompt-controls"]["handler"]
                        listed = command("list")
                        for name in directive_contents:
                            self.assertIn(name, listed)
                        self.assertEqual(
                            command("set global global.md"),
                            "Selection updated.",
                        )
                        self.assertEqual(
                            command("set platform telegram telegram.md"),
                            "Selection updated.",
                        )
                        self.assertEqual(
                            command("set model fictional-model model.md"),
                            "Selection updated.",
                        )
                        self.assertEqual(
                            json.loads(config_path.read_text(encoding="utf-8")),
                            {
                                "global": ["global.md"],
                                "platforms": {"telegram": ["telegram.md"]},
                                "models": {"fictional-model": ["model.md"]},
                            },
                        )
                        self.assertEqual(
                            command("clear model fictional-model"),
                            "Selection cleared.",
                        )
                        unchanged_config = config_path.read_bytes()
                        empty_key_result = command('set model "" model.md')
                        self.assertEqual(
                            empty_key_result,
                            "Prompt controls configuration is invalid; "
                            "no changes were made.",
                        )
                        self.assertEqual(config_path.read_bytes(), unchanged_config)

                        unsafe_result = command("set global C:\\private\\secret.md")
                        self.assertEqual(
                            unsafe_result,
                            "Prompt controls configuration is invalid; "
                            "no changes were made.",
                        )
                        self.assertNotIn("private", unsafe_result)

                        write_json(
                            config_path,
                            {"global": [], "platforms": {}, "models": {}},
                        )

                        def failing_callback(**_context):
                            raise RuntimeError("fictional middleware failure")

                        manager._middleware["llm_request"].append(failing_callback)
                        try:
                            with self.assertLogs(
                                "hermes_cli.plugins", level="WARNING"
                            ) as host_logs:
                                failure_result = apply(request)
                        finally:
                            manager._middleware["llm_request"].remove(failing_callback)
                        self.assertEqual(failure_result.payload, request)
                        self.assertFalse(failure_result.changed)
                        self.assertIn(
                            "fictional middleware failure",
                            "\n".join(host_logs.output),
                        )

                        self.assertGreaterEqual(callback_spy.call_count, 8)
                        callback_context = callback_spy.call_args_list[0].kwargs
                        self.assertEqual(
                            callback_context["api_mode"],
                            "chat_completions",
                        )
                        self.assertEqual(
                            callback_context["original_request"],
                            original_request,
                        )
                        self.assertIsNot(callback_context["request"], request)
                finally:
                    if "callback" in locals():
                        manager._middleware["llm_request"][0] = callback
                    manager.unload()


if __name__ == "__main__":
    unittest.main()
