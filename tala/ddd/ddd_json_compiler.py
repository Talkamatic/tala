import json
import xml.dom.minidom

from tala.ddd.ddd_xml_compiler import DDDXMLCompiler


class DDDJSONCompilerException(Exception):
    pass


class DDDJSONCompiler(object):
    def __init__(self):
        self._xml_compiler = DDDXMLCompiler()

    def compile_ontology(self, json_string):
        xml_string = self._convert_json_to_xml("ontology", json_string)
        return self._xml_compiler.compile_ontology(xml_string)

    def compile_domain(self, ddd_name, json_string, ontology, parser):
        xml_string = self._convert_json_to_xml("domain", json_string)
        return self._xml_compiler.compile_domain(ddd_name, xml_string, ontology, parser)

    def compile_service_interface(self, json_string):
        xml_string = self._convert_json_to_xml("service_interface", json_string)
        return self._xml_compiler.compile_service_interface(xml_string)

    def get_domain_name(self, json_string):
        data = self._parse_json(json_string)
        domain = self._get_root_node(data, "domain")
        attrs = domain.get("@", {})
        return attrs.get("name")

    def _convert_json_to_xml(self, root_name, json_string):
        data = self._parse_json(json_string)
        node = self._get_root_node(data, root_name)
        doc = xml.dom.minidom.Document()
        root = doc.createElement(root_name)
        doc.appendChild(root)
        self._apply_node(root, node)
        return doc.toxml(encoding="utf-8")

    def _parse_json(self, json_string):
        if isinstance(json_string, bytes):
            json_string = json_string.decode("utf-8")
        if isinstance(json_string, str):
            return json.loads(json_string)
        if isinstance(json_string, dict):
            return json_string
        raise DDDJSONCompilerException("Expected JSON string or dict.")

    def _get_root_node(self, data, root_name):
        if root_name in data:
            node = data[root_name]
            if node is None:
                return {}
            if isinstance(node, dict):
                return node
            raise DDDJSONCompilerException(f"Expected object for root '{root_name}'.")
        if isinstance(data, dict) and data.get("@") is not None:
            return data
        raise DDDJSONCompilerException(f"Expected root '{root_name}' in JSON.")

    def _apply_node(self, element, node):
        if not isinstance(node, dict):
            return
        attrs = node.get("@", {})
        if not isinstance(attrs, dict):
            raise DDDJSONCompilerException("Expected '@' to be an object of attributes.")
        for key, value in attrs.items():
            element.setAttribute(key, self._stringify(value))

        children = node.get("children")
        if children is not None:
            if not isinstance(children, list):
                raise DDDJSONCompilerException("Expected 'children' to be a list.")
            for child in children:
                self._append_child_from_entry(element, child)
            return

        for key, value in node.items():
            if key in ("@", "children"):
                continue
            self._append_named_child(element, key, value)

    def _append_child_from_entry(self, parent, entry):
        if not isinstance(entry, dict) or len(entry) != 1:
            raise DDDJSONCompilerException("Each child entry must be a single-key object.")
        tag, value = next(iter(entry.items()))
        self._append_named_child(parent, tag, value)

    def _append_named_child(self, parent, tag, value):
        doc = parent.ownerDocument
        if isinstance(value, list):
            for item in value:
                self._append_named_child(parent, tag, item)
            return
        element = doc.createElement(tag)
        parent.appendChild(element)
        if isinstance(value, dict):
            self._apply_node(element, value)
        elif value is None:
            return
        else:
            element.appendChild(doc.createTextNode(self._stringify(value)))

    def _stringify(self, value):
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)
