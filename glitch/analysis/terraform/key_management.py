import re
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute


class TerraformKeyManagement(TerraformSmellChecker):
    def check(self, element, file: str):
        errors = []
        if isinstance(element, AtomicUnit):
            if (element.type == "resource.azurerm_storage_account"):
                expr = "\${azurerm_storage_account\." + f"{element.name}\."
                pattern = re.compile(rf"{expr}")
                if not self.get_associated_au(file, "resource.azurerm_storage_account_customer_managed_key", "storage_account_id",
                    pattern, [""]):
                    errors.append(Error('sec_key_management', element, file, repr(element), 
                        f"Suggestion: check for a required resource 'azurerm_storage_account_customer_managed_key' " + 
                            f"associated to an 'azurerm_storage_account' resource."))
            for config in SecurityVisitor._KEY_MANAGEMENT:
                if (config['required'] == "yes" and element.type in config['au_type'] 
                    and not self.check_required_attribute(element.attributes, config['parents'], config['attribute'])):
                    errors.append(Error('sec_key_management', element, file, repr(element), 
                        f"Suggestion: check for a required attribute with name '{config['msg']}'."))
                    
            def check_attribute(attribute: Attribute, parent_name: str):
                for config in SecurityVisitor._KEY_MANAGEMENT:
                    if (attribute.name == config['attribute'] and element.type in config['au_type']
                        and parent_name in config['parents'] and config['values'] != [""]):
                        if ("any_not_empty" in config['values'] and attribute.value.lower() == ""):
                            errors.append(Error('sec_key_management', attribute, file, repr(attribute)))
                            break
                        elif ("any_not_empty" not in config['values'] and not attribute.has_variable and 
                            attribute.value.lower() not in config['values']):
                            errors.append(Error('sec_key_management', attribute, file, repr(attribute)))
                            break

                if (attribute.name == "rotation_period" and element.type == "resource.google_kms_crypto_key"):
                    expr1 = r'\d+\.\d{0,9}s'
                    expr2 = r'\d+s'
                    if (re.search(expr1, attribute.value) or re.search(expr2, attribute.value)):
                        if (int(attribute.value.split("s")[0]) > 7776000):
                            errors.append(Error('sec_key_management', attribute, file, repr(attribute)))
                    else:
                        errors.append(Error('sec_key_management', attribute, file, repr(attribute)))
                elif (attribute.name == "kms_master_key_id" and ((element.type == "resource.aws_sqs_queue"
                    and attribute.value == "alias/aws/sqs") or  (element.type == "resource.aws_sns_queue"
                    and attribute.value == "alias/aws/sns"))):
                    errors.append(Error('sec_key_management', attribute, file, repr(attribute)))

                for attr_child in attribute.keyvalues:
                    check_attribute(attr_child, attribute.name)

            for attribute in element.attributes:
                check_attribute(attribute, "")
                    
        return errors