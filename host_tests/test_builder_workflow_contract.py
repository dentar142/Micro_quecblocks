import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER_HTML = (
    ROOT
    / "builder"
    / "easy_api_main_builder_microblocks.html"
)


def _balanced_body(source, marker, opening="{", closing="}"):
    start = source.find(marker)
    if start < 0:
        raise AssertionError("missing JavaScript marker: " + marker)
    delimiter = source.find(opening, start + len(marker))
    if delimiter < 0:
        raise AssertionError("missing opening delimiter after: " + marker)
    depth = 0
    quote = None
    escaped = False
    line_comment = False
    block_comment = False
    for index in range(delimiter, len(source)):
        char = source[index]
        next_char = source[index + 1] if index + 1 < len(source) else ""
        if line_comment:
            if char in "\\r\\n":
                line_comment = False
            continue
        if block_comment:
            if char == "*" and next_char == "/":
                block_comment = False
            continue
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char == "/" and next_char == "/":
            line_comment = True
            continue
        if char == "/" and next_char == "*":
            block_comment = True
            continue
        if char in ("'", '"', "`"):
            quote = char
        elif char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                return source[delimiter + 1:index]
    raise AssertionError("unterminated JavaScript block after: " + marker)


def _const_array(source, name):
    body = _balanced_body(source, "const " + name + " =", "[", "]")
    return re.findall(r'["\']([A-Za-z_][A-Za-z0-9_]*)["\']', body)


def _from_marker(source, marker):
    start = source.find(marker)
    if start < 0:
        raise AssertionError("missing JavaScript marker: " + marker)
    return source[start:]


def _const_object_pairs(source, name):
    body = _balanced_body(source, "const " + name + " =")
    return dict(re.findall(
        r'\b([A-Za-z_][A-Za-z0-9_]*)\s*:\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']',
        body,
    ))


class BuilderWorkflowContractTests(unittest.TestCase):
    """Zero-dependency contracts for the MicroBlocks-to-main.py workflow."""

    @classmethod
    def setUpClass(cls):
        cls.source = BUILDER_HTML.read_text(encoding="utf-8")

    def test_single_builder_keeps_five_way_direction_contract(self):
        self.assertIn('readanjian_direction: "anjian"', self.source)
        self.assertIn('{ key: "button_direction",', self.source)
        for key in ("button", "button_adc", "button_direction", "key_status"):
            self.assertIn('"' + key + '"', self.source)

    def test_module_switch_catalog_matches_startup_panel(self):
        module_catalog = set(re.findall(r'\["([a-z0-9_]+)","[^"\n]+"\]', self.source[self.source.find("const MODULE_CATEGORIES ="):self.source.find("const API_CATEGORIES =")]))
        panel = _balanced_body(self.source, "function renderModulePanel()")
        panel_modules = set(re.findall(r'\["([a-z0-9_]+)",\s*"[^"\n]+"\]', panel))
        expected = {"led", "anjian", "timer", "hmi", "guangmin", "i2c", "wenhumi", "jiasudu", "gpio", "pwm", "fengmingqi", "lcd", "spi", "uart", "rs232", "rs485", "cunchu", "yinpin", "lte", "ble", "gnss", "lbs"}
        self.assertEqual(module_catalog, expected)
        self.assertEqual(panel_modules, expected)

    def test_parameterized_apis_cannot_be_zero_argument_blocks(self):
        parameterized = _const_object_pairs(self.source, "API_TO_PARAM_PRESET")
        zero_argument = set(_const_array(self.source, "ZERO_ARG_APIS"))
        conflicts = sorted(set(parameterized) & zero_argument)
        self.assertEqual(
            conflicts,
            [],
            "parameterized APIs must not bypass paramapi inputs: " + ", ".join(conflicts),
        )

        palette = _balanced_body(self.source, "function renderApiPalette()")
        self.assertIn("API_TO_PARAM_PRESET[api]", palette)
        self.assertIn('data-action="add-param-api"', palette)
        self.assertIn('defaultBlock("paramapi"', self.source)

    def test_sdcard_and_common_parameter_apis_are_draggable(self):
        parameterized = _const_object_pairs(self.source, "API_TO_PARAM_PRESET")
        expected = {
            "listfiles": "file_list",
            "storageinfo": "storage_info",
            "makedir": "dir_make",
            "removedir": "dir_remove",
            "setled": "led_set",
            "showlcd": "lcd_text",
            "senduart": "uart_send",
            "keytext": "key_text",
            "iskey": "key_is",
        }
        for api_name, preset_name in expected.items():
            self.assertEqual(parameterized.get(api_name), preset_name)

        restrict = _balanced_body(self.source, "function restrictToUniknect()")
        self.assertIn("PARAM_API_PRESETS.some", restrict)
        self.assertNotIn('item.dataset.paramKey === "i2c_scan"', restrict)

        for key in ("file_list", "storage_info", "dir_make", "dir_remove"):
            self.assertIn('{ key: "' + key + '"', self.source)
            self.assertIn('if (key === "' + key + '")', self.source)

    def test_generated_program_checks_runtime_api_surface_before_hardware_calls(self):
        generator = _balanced_body(self.source, "function generateMainCode()")
        self.assertIn("_REQUIRED_EASY_API", generator)
        self.assertIn("_MISSING_EASY_API", generator)
        self.assertIn("upload the complete runtime/starter", generator)

    def test_builder_api_calls_exist_in_runtime_parts(self):
        runtime = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (ROOT / "runtime" / "starter" / "easy_api_parts").glob("*.py")
        )
        runtime_names = set(re.findall(r"^def\s+([A-Za-z_]\w*)\s*\(", runtime, re.MULTILINE))
        builder_calls = set(re.findall(r"api\.([A-Za-z_]\w*)\s*\(", self.source))
        self.assertEqual(sorted(builder_calls - runtime_names), [])

    def test_five_way_key_contract_is_exposed_and_parameterized(self):
        self.assertIn('lastanjian: "读取最近按键事件"', self.source)
        self.assertIn('api.keytext(api.lastanjian())', self.source)
        parameterized = _const_object_pairs(self.source, "API_TO_PARAM_PRESET")
        self.assertEqual(parameterized.get("waitkey"), "wait_key")
        meta = _from_marker(self.source, "const PARAM_API_META =")
        self.assertIn("wait_key:", meta)
        self.assertIn('aOptions:', meta)
        self.assertIn('cOptions:', meta)
        self.assertIn('key === "wait_key"', self.source)

    def test_legacy_key_status_state_is_migrated(self):
        normalizer = _balanced_body(self.source, "function normalizeSavedBlock(")
        self.assertIn('normalized.readKey === "key_status"', normalizer)
        self.assertIn('normalized.readExpr = "api.keytext(api.lastanjian())"', normalizer)

    def test_all_read_presets_remain_selectable(self):
        preset_body = _balanced_body(self.source, "const READ_PRESETS =", "[", "]")
        read_keys = set(re.findall(r'\bkey\s*:\s*["\']([^"\']+)["\']', preset_body))
        self.assertGreaterEqual(len(read_keys), 20, "the EC200U read catalog should stay complete")

        restrict = _balanced_body(self.source, "function restrictBlockInputs()")
        self.assertNotIn(
            'data-field="readKey"',
            restrict,
            "module restriction must not remove LTE/GNSS/BLE/UART read presets",
        )

    def test_ordinary_api_dependencies_use_one_complete_mapping(self):
        dependency_map = _const_object_pairs(self.source, "API_MODULE_REQUIREMENTS")
        expected = {
            "readguangmin": "guangmin",
            "clearlcd": "lcd",
            "senduart": "uart",
            "readlte": "lte",
            "networkstatus": "lte",
            "readgnss": "gnss",
            "readlbs": "lbs",
            "readble": "ble",
        }
        self.assertEqual(
            {name: dependency_map.get(name) for name in expected},
            expected,
            "ordinary APIs need a central module dependency table",
        )
        self.assertEqual(
            dependency_map.get("readadc"),
            "guangmin",
            "ADC pin reads use the shared 光敏 ADC / guangmin startup switch",
        )

        validator = _from_marker(self.source, "function validateBuilder()")
        api_branch_start = validator.find('block.type === "api"')
        self.assertGreaterEqual(api_branch_start, 0)
        api_branch = validator[api_branch_start:]
        self.assertIn("API_MODULE_REQUIREMENTS", api_branch)
        self.assertRegex(api_branch, r"requireModule\s*\(")

    def test_nested_api_blocks_share_a_phase_and_placement_guard(self):
        emitter = _balanced_body(self.source, "function emitBlock(")
        self.assertNotIn(
            'phase === "fast" && block.placement !== "startup"',
            emitter,
            "fast containers must not force slow APIs into the fast loop",
        )
        self.assertNotIn(
            'phase !== "fast" && block.placement !== "startup" && block.placement !== "fast"',
            emitter,
            "slow generation must not silently drop fast APIs",
        )

        param_position = emitter.find('block.type === "paramapi"')
        api_position = emitter.find('block.type === "api"')
        self.assertGreaterEqual(param_position, 0)
        self.assertGreaterEqual(api_position, 0)
        param_branch = emitter[param_position:api_position]
        api_branch = emitter[api_position:]
        self.assertRegex(param_branch, r"shouldEmitBlock\s*\(\s*block\s*,\s*phase\s*\)")
        self.assertRegex(api_branch, r"shouldEmitBlock\s*\(\s*block\s*,\s*phase\s*\)")

        validator = _from_marker(self.source, "function validateBuilder()")
        self.assertRegex(validator, r"enclosingPhase\s*\(")
        self.assertRegex(validator, r"blockExecutionPlacement\s*\(")

    def test_lcd_canvas_is_not_appended_to_both_loop_phases(self):
        generator = _balanced_body(self.source, "function generateMainCode()")
        fast_append = "fast.push.apply(fast, canvasLines)" in generator
        slow_append = "slow.push.apply(slow, canvasLines)" in generator
        self.assertFalse(
            fast_append and slow_append,
            "LCD canvas commands must have one deterministic execution phase",
        )
        self.assertTrue(
            fast_append or slow_append or "canvasLines" not in generator,
            "LCD canvas commands must either use one phase or a replacement path",
        )

    def test_copy_and_download_export_even_when_diagnostics_have_errors(self):
        copy_body = _balanced_body(self.source, "async function copyCode()")
        download_body = _balanced_body(self.source, "function downloadCode()")
        self.assertIn("lastGeneratedCode", copy_body)
        self.assertIn("lastGeneratedCode", download_body)
        self.assertIn("已复制 main.py；同时发现", copy_body)
        self.assertIn("已下载 main.py；同时发现", download_body)
        self.assertNotIn("已阻止复制", copy_body)
        self.assertNotIn("已阻止下载", download_body)

    def test_generation_failure_is_visible_and_keeps_debug_code(self):
        generator = _balanced_body(self.source, "function generateAndRender(options)")
        self.assertIn("main.py generation failed", generator)
        self.assertIn("生成代码时发生异常", generator)
        self.assertIn("codePreview", generator)

    def test_location_and_return_value_contracts(self):
        requirements = _const_object_pairs(self.source, "API_MODULE_REQUIREMENTS")
        self.assertEqual(requirements.get("readlocation"), "gnss_or_lbs")
        self.assertIn("API_RETURN_APIS", self.source)
        self.assertIn("apiOutputVar", self.source)
        emitter = _balanced_body(self.source, "function apiCallLine(")
        self.assertIn("apiOutputVar", emitter)

    def test_portal_menu_repositions_by_owner_id(self):
        positioner = _balanced_body(self.source, "function positionOpenToolPanels()")
        self.assertIn("[data-owner-id]", positioner)
        self.assertIn("panel.dataset.ownerId", positioner)

    def test_condition_module_dependencies_are_checked(self):
        validator = _from_marker(self.source, "function validateBuilder()")
        self.assertIn("条件中的 GPIO 调用", validator)
        self.assertIn("条件中的按键调用", validator)
        self.assertIn(
            'block.conditionMode === "preset"',
            validator,
            "structured conditions must ignore stale legacy expression text",
        )

    def test_structural_and_action_blocks_inherit_the_container_phase(self):
        placement = _balanced_body(self.source, "function blockExecutionPlacement(")
        for block_type in ("if", "fastloop", "slowloop", "forever", "button"):
            self.assertIn(
                '"' + block_type + '"',
                placement,
                block_type + " blocks must not inherit the ordinary slow default",
            )

        normalizer = _balanced_body(self.source, "function normalizeSavedBlock(")
        self.assertIn('normalized.placement = ""', normalizer)
        self.assertIn('"fastloop"', normalizer)

    def test_lcd_canvas_scene_is_initialized_after_easy_api(self):
        generator = _balanced_body(self.source, "function generateMainCode()")
        self.assertIn('"    api.lcdfill(\\"black\\")"', generator)
        self.assertIn("lcdDesign.map(item => lcdDesignCodeLine(item))", generator)
        self.assertLess(
            generator.find('"api.init()"'),
            generator.find('"    api.lcdfill(\\"black\\")"'),
            "LCD canvas drawing must happen after api.init/module setup",
        )

    def test_lcd_property_edit_does_not_rebuild_active_form_for_each_number(self):
        designer = _from_marker(self.source, "function renderLcdDesigner()")
        self.assertIn("function renderLcdCanvas()", self.source)
        self.assertIn("if (key === \"type\" || key === \"color\") renderLcdDesigner();", self.source)
        self.assertIn("renderLcdCanvas(); generateAndRender({ deferHistory: true });", self.source)

    def test_reporter_and_predicate_support_nested_input_nodes(self):
        self.assertIn("function reporterExpression(node, fallback)", self.source)
        self.assertIn("function predicateExpression(node)", self.source)
        self.assertIn("function reporterNodeFromBlock(block)", self.source)
        self.assertIn("function predicateNodeFromBlock(block)", self.source)
        emitter = _balanced_body(self.source, "function emitBlock(")
        self.assertIn("reporterNodeFromBlock(block)", emitter)
        self.assertIn("reporterExpression(node", emitter)
        self.assertIn("conditionExpr(block)", emitter)
        self.assertIn("reporterReferencedVariables(reporterNodeFromBlock(block)", self.source)
        self.assertIn("reporterReferencedVariables(predicateNodeFromBlock(block)", self.source)

    def test_event_and_forever_have_single_scheduler_contract(self):
        emitter = _balanced_body(self.source, "function emitBlock(")
        generator = _balanced_body(self.source, "function generateMainCode()")
        self.assertIn('block.type === "event"', emitter)
        self.assertIn('block.type === "forever"', emitter)
        self.assertIn('explicitForever.length === 1 ? "while True:"', generator)
        self.assertIn('explicitForever[0].children', generator)
        validator = _from_marker(self.source, "function validateBuilder()")
        self.assertIn("永久循环只能放在根级", validator)
        self.assertIn("最多只能有一个根级永久循环", validator)

    def test_new_types_are_in_the_builder_vocabulary(self):
        types = set(_const_array(self.source, "BUILDER_TYPES"))
        self.assertTrue({"reporter", "predicate", "event", "forever"}.issubset(types))
        self.assertIn('reporterKind: "api"', self.source)
        self.assertIn('predicateKind: ""', self.source)


if __name__ == "__main__":
    unittest.main()
