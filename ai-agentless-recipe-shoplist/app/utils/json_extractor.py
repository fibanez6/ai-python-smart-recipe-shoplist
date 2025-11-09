import re
from typing import Any, Dict, List, Optional, Union

import jmespath
from pydantic import BaseModel


class JSONExtractor:
    """
    Universal JSON extractor supporting multiple extraction patterns:
    
    Features:
    - JMESPath and dot notation paths
    - Wildcard array extraction (e.g., "data[*].name")  
    - Field selection with "fields": [...]
    - Array filtering (limit, regex, custom filters)
    - Nested object field extraction
    - Mixed rule syntax support
    - Null value cleanup
    - Optional Pydantic model conversion
    
    Example rules:
        {
            "data": {
                "fields": ["name", "price"],
                "categories[*].name": True,
                "assets": {"limit": 1, "fields": ["url"]}
            }
        }
    """

    def __init__(self, rules: Dict[str, Any], model: Optional[BaseModel] = None):
        """
        Initialize JSONExtractor with extraction rules.
        
        Args:
            rules: Dictionary describing extraction rules and patterns
            model: Optional Pydantic model to convert output into
        """
        self.rules = rules
        self.model = model
        # Pre-compile JMESPath expressions for performance (skip special paths)
        self._compiled = {
            path: jmespath.compile(path) 
            for path in rules.keys() 
            if path not in [".", "@"] and not self._is_mixed_instruction(rules[path])
        }
    
    def _is_mixed_instruction(self, instruction: Any) -> bool:
        """Check if instruction contains mixed patterns (fields + sub-rules)."""
        return (isinstance(instruction, dict) and 
                "fields" in instruction and 
                any(key not in ["fields", "limit", "regex", "default", "filter"] 
                    for key in instruction.keys()))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(self, data: Union[Dict, List[Dict]]) -> Union[Dict, List[Dict]]:
        """
        Extract data according to configured rules.
        
        Args:
            data: Input data - either a dict or list of dicts
            
        Returns:
            Extracted data with same structure (dict or list of dicts)
        """
        if isinstance(data, list):
            result = [self._extract_one(item) for item in data]
        else:
            result = self._extract_one(data)

        return self._convert_model(result)

    # ------------------------------------------------------------------
    # Core Extraction Logic
    # ------------------------------------------------------------------

    def _extract_one(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from a single item according to all rules."""
        output = {}
        
        for path, instruction in self.rules.items():
            self._process_rule(item, path, instruction, output)
        
        return self._cleanup_nulls(output)
    
    def _process_rule(self, item: Dict[str, Any], path: str, instruction: Any, output: Dict[str, Any]) -> None:
        """
        Process a single extraction rule.
        
        Args:
            item: Source data item
            path: JSONPath or field name  
            instruction: Rule configuration
            output: Target output dictionary
        """
        # Root-level field extraction: "@": {"fields": [...]}
        if path == "@" and isinstance(instruction, dict) and "fields" in instruction:
            self._extract_root_fields(item, instruction["fields"], output)
            return
        
        # Mixed instructions: fields + sub-rules in same object
        if self._is_mixed_instruction(instruction):
            self._process_mixed_instruction(item, path, instruction, output)
            return
        
        # Simple nested instruction: {"fields": [...], "limit": 1, ...}
        if isinstance(instruction, dict) and self._is_simple_instruction(instruction):
            self._process_simple_instruction(item, path, instruction, output)
            return
        
        # Standard path-based extraction
        self._process_path_extraction(item, path, instruction, output)
    
    def _is_simple_instruction(self, instruction: Dict[str, Any]) -> bool:
        """Check if instruction is a simple nested instruction without sub-rules."""
        instruction_keys = {"fields", "limit", "regex", "default", "filter"}
        return any(key in instruction for key in instruction_keys)
    
    def _extract_root_fields(self, item: Dict[str, Any], fields: List[str], output: Dict[str, Any]) -> None:
        """Extract specified fields from root level of item."""
        for field in fields:
            if field in item:
                output[field] = item[field]
    
    def _process_mixed_instruction(self, item: Dict[str, Any], path: str, instruction: Dict[str, Any], output: Dict[str, Any]) -> None:
        """Process instruction containing both fields and sub-rules."""
        if path not in item:
            return
            
        # Process main fields first
        self._process_simple_instruction(item, path, instruction, output)
        
        # Process sub-rules
        for sub_path, sub_instruction in instruction.items():
            if sub_path not in ["fields", "limit", "regex", "default", "filter"]:
                self._process_sub_rule(item[path], sub_path, sub_instruction, output, path)
    
    def _process_simple_instruction(self, item: Dict[str, Any], path: str, instruction: Dict[str, Any], output: Dict[str, Any]) -> None:
        """Process simple nested instruction on a specific path."""
        if path not in item:
            return
            
        value = item[path]
        processed_value = self._process_value(value, instruction)
        output[path] = processed_value
    
    def _process_path_extraction(self, item: Dict[str, Any], path: str, instruction: Any, output: Dict[str, Any]) -> None:
        """Process standard JMESPath-based extraction."""
        if path not in self._compiled:
            return
            
        # Extract value using appropriate method
        if "[*]" in path:
            value = self._extract_wildcard_path(item, path, instruction)
        else:
            value = self._compiled[path].search(item)

        # Handle missing values
        if value is None:
            if isinstance(instruction, dict) and "default" in instruction:
                value = instruction["default"]
            else:
                return

        # Process and assign value
        processed_value = self._process_value(value, instruction)
        self._assign(output, path, processed_value)
    

    
    # ------------------------------------------------------------------
    # Sub-rule Processing
    # ------------------------------------------------------------------
    
    def _process_sub_rule(self, parent_value: Union[List, Dict], sub_path: str, sub_instruction: Any, 
                         output: Dict[str, Any], parent_path: str) -> None:
        """
        Process sub-rules within mixed instructions.
        
        Args:
            parent_value: Value from parent path
            sub_path: Path of the sub-rule 
            sub_instruction: Sub-rule configuration
            output: Target output dictionary
            parent_path: Original parent path name
        """
        if isinstance(parent_value, list):
            self._process_array_sub_rule(parent_value, sub_path, sub_instruction, output, parent_path)
        elif isinstance(parent_value, dict):
            self._process_dict_sub_rule(parent_value, sub_path, sub_instruction, output, parent_path)
    
    def _process_array_sub_rule(self, array_value: List, sub_path: str, sub_instruction: Any,
                               output: Dict[str, Any], parent_path: str) -> None:
        """Process sub-rule for array values."""
        new_items = []
        
        for i, item in enumerate(array_value):
            if isinstance(item, dict):
                # Get existing processed item or create new one
                if parent_path in output and isinstance(output[parent_path], list) and i < len(output[parent_path]):
                    new_item = dict(output[parent_path][i])
                else:
                    new_item = {}
                
                self._apply_sub_rule_to_item(item, sub_path, sub_instruction, new_item)
                new_items.append(new_item)
            else:
                new_items.append(item)
        
        # Merge with existing output
        self._merge_array_output(output, parent_path, new_items)
    
    def _process_dict_sub_rule(self, dict_value: Dict, sub_path: str, sub_instruction: Any,
                              output: Dict[str, Any], parent_path: str) -> None:
        """Process sub-rule for dictionary values."""
        if parent_path not in output:
            output[parent_path] = {}
        self._apply_sub_rule_to_item(dict_value, sub_path, sub_instruction, output[parent_path])
    
    def _merge_array_output(self, output: Dict[str, Any], parent_path: str, new_items: List) -> None:
        """Merge new items with existing output array."""
        if parent_path in output and isinstance(output[parent_path], list):
            merged_items = []
            for i, existing_item in enumerate(output[parent_path]):
                if (i < len(new_items) and 
                    isinstance(existing_item, dict) and isinstance(new_items[i], dict)):
                    merged_item = dict(existing_item)
                    merged_item.update(new_items[i])
                    merged_items.append(merged_item)
                elif i < len(new_items):
                    merged_items.append(new_items[i])
                else:
                    merged_items.append(existing_item)
            output[parent_path] = merged_items
        else:
            output[parent_path] = new_items
    
    def _apply_sub_rule_to_item(self, item: Dict[str, Any], sub_path: str, sub_instruction: Any, target: Dict[str, Any]) -> None:
        """
        Apply a sub-rule to a single data item.
        
        Args:
            item: Source data item
            sub_path: Path within the item
            sub_instruction: Rule configuration  
            target: Target dictionary to update
        """
        # Wildcard array paths: "categories[*].name" (check before general field check)
        if "[*]." in sub_path:
            self._extract_wildcard_field(item, sub_path, target)
            return
            
        if sub_path not in item:
            return
        
        # Nested object instructions: {"limit": 1, "fields": ["url"]}
        elif isinstance(sub_instruction, dict):
            processed_value = self._process_value(item[sub_path], sub_instruction)
            target[sub_path] = processed_value
        
        # Field list: ["field1", "field2", ...]
        elif isinstance(sub_instruction, list):
            self._extract_fields_from_object(item, sub_path, sub_instruction, target)
        
        # Boolean flag: True
        elif sub_instruction is True:
            target[sub_path] = item[sub_path]
    
    def _extract_wildcard_field(self, item: Dict[str, Any], wildcard_path: str, target: Dict[str, Any]) -> None:
        """Extract field from array using wildcard syntax."""
        array_field, target_field = wildcard_path.split("[*].", 1)
        
        if array_field in item and isinstance(item[array_field], list):
            extracted_values = [
                array_item[target_field] 
                for array_item in item[array_field] 
                if isinstance(array_item, dict) and target_field in array_item
            ]
            
            # Use clean field name
            clean_name = array_field if target_field == "name" else f"{array_field}_{target_field}"
            target[clean_name] = extracted_values
    
    def _extract_fields_from_object(self, item: Dict[str, Any], sub_path: str, fields: List[str], target: Dict[str, Any]) -> None:
        """Extract specific fields from a nested object."""
        source_obj = item[sub_path]
        
        if isinstance(source_obj, dict):
            target[sub_path] = {
                field: source_obj[field] 
                for field in fields 
                if field in source_obj
            }
        else:
            target[sub_path] = source_obj
    
    # ------------------------------------------------------------------
    # Value Processing
    # ------------------------------------------------------------------
    
    def _process_value(self, value: Any, instruction: Union[Dict[str, Any], Any]) -> Any:
        """
        Process extracted value according to instruction rules.
        
        Args:
            value: Extracted value to process
            instruction: Processing rules
            
        Returns:
            Processed value
        """
        if not isinstance(instruction, dict):
            return value
            
        # Apply regex filtering first
        if "regex" in instruction and isinstance(value, str):
            if not re.compile(instruction["regex"]).search(value):
                return None
        
        # Handle different value types
        if isinstance(value, dict):
            return self._process_dict_value(value, instruction)
        elif isinstance(value, list):
            return self._process_array_value(value, instruction)
        else:
            return value
    
    def _process_dict_value(self, value: Dict[str, Any], instruction: Dict[str, Any]) -> Dict[str, Any]:
        """Process dictionary value with field selection."""
        if "fields" in instruction:
            return {
                field: value[field] 
                for field in instruction["fields"] 
                if field in value
            }
        return value
    
    def _process_array_value(self, value: List[Any], instruction: Dict[str, Any]) -> List[Any]:
        """Process array value with filtering, limiting, and field selection."""
        processed = value
        
        # Apply regex filter to array elements
        if "regex" in instruction:
            pattern = re.compile(instruction["regex"])
            processed = [item for item in processed if isinstance(item, str) and pattern.search(item)]
        
        # Apply custom filter function
        if "filter" in instruction:
            processed = list(filter(instruction["filter"], processed))
        
        # Apply length limit
        if "limit" in instruction:
            processed = processed[:instruction["limit"]]
        
        # Apply field selection to array elements
        if "fields" in instruction:
            processed = self._extract_fields_from_array(processed, instruction["fields"])
        
        return processed
    
    def _extract_fields_from_array(self, array: List[Any], fields: List[Union[str, Dict[str, List[str]]]]) -> List[Dict[str, Any]]:
        """Extract specified fields from each dict in array."""
        result = []
        
        for item in array:
            if not isinstance(item, dict):
                result.append(item)
                continue
                
            extracted = {}
            
            for field_spec in fields:
                if isinstance(field_spec, dict):
                    # Nested field spec: {"price": ["amount", "display"]}
                    for field_name, subfields in field_spec.items():
                        if field_name in item and isinstance(item[field_name], dict):
                            extracted[field_name] = {
                                sf: item[field_name][sf] 
                                for sf in subfields 
                                if sf in item[field_name]
                            }
                        elif field_name in item:
                            extracted[field_name] = item[field_name]
                
                elif isinstance(field_spec, str):
                    if "[*]." in field_spec:
                        # Wildcard path: "categories[*].name" 
                        array_field, target_field = field_spec.split("[*].", 1)
                        if array_field in item and isinstance(item[array_field], list):
                            extracted_values = [
                                array_item[target_field] 
                                for array_item in item[array_field] 
                                if isinstance(array_item, dict) and target_field in array_item
                            ]
                            clean_name = array_field if target_field == "name" else f"{array_field}_{target_field}"
                            extracted[clean_name] = extracted_values
                    elif field_spec in item:
                        extracted[field_spec] = item[field_spec]
            
            result.append(extracted)
        
        return result

    # ------------------------------------------------------------------
    # Wildcard Path Handling
    # ------------------------------------------------------------------

    def _extract_wildcard_path(self, item: Dict[str, Any], path: str, instruction: Any) -> List[Any]:
        """
        Handle wildcard paths like 'data[*].price' for array field extraction.
        
        Args:
            item: Source data item
            path: Wildcard path (e.g., "data[*].price")
            instruction: Processing rules
            
        Returns:
            List of extracted values
        """
        if "[*]." not in path:
            return self._compiled[path].search(item)
            
        array_path, field_path = path.split("[*].", 1)
        
        if array_path not in item or not isinstance(item[array_path], list):
            return []
        
        results = []
        for array_item in item[array_path]:
            if not isinstance(array_item, dict):
                continue
                
            # Extract field value (supports nested paths)
            if "." in field_path:
                field_value = jmespath.compile(field_path).search(array_item)
            else:
                field_value = array_item.get(field_path)
            
            if field_value is not None:
                # Apply field filtering if specified
                if isinstance(instruction, dict) and "fields" in instruction and isinstance(field_value, dict):
                    field_value = {
                        f: field_value[f] 
                        for f in instruction["fields"] 
                        if f in field_value
                    }
                results.append(field_value)
        
        return results

    # ------------------------------------------------------------------
    # Utility Methods
    # ------------------------------------------------------------------

    def _assign(self, output: Dict[str, Any], path: str, value: Any) -> None:
        """
        Assign value to nested dictionary path.
        
        Args:
            output: Target dictionary
            path: Dot-separated path (e.g., "data.items")
            value: Value to assign
        """
        keys = path.replace("[*]", "").split(".")
        current = output
        
        # Navigate to parent key
        for key in keys[:-1]:
            if isinstance(current, dict):
                current = current.setdefault(key, {})
            else:
                return  # Cannot assign to non-dict
        
        # Set final value
        if isinstance(current, dict):
            current[keys[-1]] = value

    def _cleanup_nulls(self, obj: Any) -> Any:
        """
        Remove null values from nested structures recursively.
        
        Args:
            obj: Object to clean
            
        Returns:
            Object with null values removed
        """
        if isinstance(obj, dict):
            return {
                key: self._cleanup_nulls(value)
                for key, value in obj.items()
                if value is not None
            }
        elif isinstance(obj, list):
            return [
                self._cleanup_nulls(item) 
                for item in obj 
                if item is not None
            ]
        return obj

    def _convert_model(self, data: Union[Dict, List[Dict]]) -> Union[Dict, List[Dict]]:
        """
        Convert extracted data to Pydantic model if specified.
        
        Args:
            data: Extracted data
            
        Returns:
            Data converted to model or original data
        """
        if self.model is None:
            return data

        if isinstance(data, list):
            return [self.model(**item) for item in data]
        return self.model(**data)
