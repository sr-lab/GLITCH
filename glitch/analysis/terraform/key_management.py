import re
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, Variable


class TerraformKeyManagement(TerraformSmellChecker):
    def check(self, element, file: str, au_type = None, parent_name = ""):
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
                    
        elif isinstance(element, Attribute) or isinstance(element, Variable):
            for config in SecurityVisitor._KEY_MANAGEMENT:
                if (element.name == config['attribute'] and au_type in config['au_type']
                    and parent_name in config['parents'] and config['values'] != [""]):
                    if ("any_not_empty" in config['values'] and element.value.lower() == ""):
                        errors.append(Error('sec_key_management', element, file, repr(element)))
                        break
                    elif ("any_not_empty" not in config['values'] and not element.has_variable and 
                        element.value.lower() not in config['values']):
                        errors.append(Error('sec_key_management', element, file, repr(element)))
                        break

            if (element.name == "rotation_period" and au_type == "resource.google_kms_crypto_key"):
                expr1 = r'\d+\.\d{0,9}s'
                expr2 = r'\d+s'
                if (re.search(expr1, element.value) or re.search(expr2, element.value)):
                    if (int(element.value.split("s")[0]) > 7776000):
                        errors.append(Error('sec_key_management', element, file, repr(element)))
                else:
                    errors.append(Error('sec_key_management', element, file, repr(element)))
            elif (element.name == "kms_master_key_id" and ((au_type == "resource.aws_sqs_queue"
                and element.value == "alias/aws/sqs") or  (au_type == "resource.aws_sns_queue"
                and element.value == "alias/aws/sns"))):
                errors.append(Error('sec_key_management', element, file, repr(element)))
        return errors