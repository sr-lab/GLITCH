import re
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, Variable


class TerraformAccessControl(TerraformSmellChecker):
    def check(self, element, file: str, code, elem_name: str, elem_value: str = "", au_type = None, parent_name = ""):
        errors = []
        if isinstance(element, AtomicUnit):
            if (element.type == "resource.aws_api_gateway_method"):
                http_method = self.check_required_attribute(element.attributes, [""], 'http_method')
                authorization =self.check_required_attribute(element.attributes, [""], 'authorization')
                if (http_method and authorization):
                    if (http_method.value.lower() == 'get' and authorization.value.lower() == 'none'):
                        api_key_required = self.check_required_attribute(element.attributes, [""], 'api_key_required')
                        if api_key_required and f"{api_key_required.value}".lower() != 'true':
                            errors.append(Error('sec_access_control', api_key_required, file, repr(api_key_required)))
                        elif not api_key_required:
                            errors.append(Error('sec_access_control', element, file, repr(element), 
                            f"Suggestion: check for a required attribute with name 'api_key_required'."))
                elif (http_method and not authorization):
                        errors.append(Error('sec_access_control', element, file, repr(element), 
                            f"Suggestion: check for a required attribute with name 'authorization'."))
            elif (element.type == "resource.github_repository"):
                visibility = self.check_required_attribute(element.attributes, [""], 'visibility')
                if visibility is not None:
                    if visibility.value.lower() not in ["private", "internal"]:
                        errors.append(Error('sec_access_control', visibility, file, repr(visibility)))
                else:
                    private = self.check_required_attribute(element.attributes, [""], 'private')
                    if private is not None:
                        if f"{private.value}".lower() != "true":
                            errors.append(Error('sec_access_control', private, file, repr(private)))
                    else:
                        errors.append(Error('sec_access_control', element, file, repr(element), 
                            f"Suggestion: check for a required attribute with name 'visibility' or 'private'."))
            elif (element.type == "resource.google_sql_database_instance"):
                errors += self.check_database_flags(element, file, 'sec_access_control', "cross db ownership chaining", "off")
            elif (element.type == "resource.aws_s3_bucket"):
                expr = "\${aws_s3_bucket\." + f"{elem_name}\."
                pattern = re.compile(rf"{expr}")
                if not self.get_associated_au(code, file, "resource.aws_s3_bucket_public_access_block", "bucket", pattern, [""]):
                    errors.append(Error('sec_access_control', element, file, repr(element), 
                        f"Suggestion: check for a required resource 'aws_s3_bucket_public_access_block' " + 
                            f"associated to an 'aws_s3_bucket' resource."))

            for config in SecurityVisitor._ACCESS_CONTROL_CONFIGS:
                if (config['required'] == "yes" and element.type in config['au_type']
                    and not self.check_required_attribute(element.attributes, config['parents'], config['attribute'])):
                    errors.append(Error('sec_access_control', element, file, repr(element), 
                        f"Suggestion: check for a required attribute with name '{config['msg']}'."))
                    
        elif isinstance(element, Attribute) or isinstance(element, Variable):
            for item in SecurityVisitor._POLICY_KEYWORDS:
                if item.lower() == elem_name:
                    for config in SecurityVisitor._POLICY_ACCESS_CONTROL:
                        expr = config['keyword'].lower() + "\s*" + config['value'].lower()
                        pattern = re.compile(rf"{expr}")
                        allow_expr = "\"effect\":" + "\s*" + "\"allow\""
                        allow_pattern = re.compile(rf"{allow_expr}")
                        if re.search(pattern, elem_value) and re.search(allow_pattern, elem_value):
                            errors.append(Error('sec_access_control', element, file, repr(element)))
                            break

            if (re.search(r"actions\[\d+\]", elem_name) and parent_name == "permissions" 
                and au_type == "resource.azurerm_role_definition" and elem_value == "*"):
                errors.append(Error('sec_access_control', element, file, repr(element)))
            elif (((re.search(r"members\[\d+\]", elem_name) and au_type == "resource.google_storage_bucket_iam_binding")
                or (elem_name == "member" and au_type == "resource.google_storage_bucket_iam_member"))
                and (elem_value == "allusers" or elem_value == "allauthenticatedusers")):
                errors.append(Error('sec_access_control', element, file, repr(element)))
            elif (elem_name == "email" and parent_name == "service_account" 
                and au_type == "resource.google_compute_instance"
                and re.search(r".-compute@developer.gserviceaccount.com", elem_value)):
                errors.append(Error('sec_access_control', element, file, repr(element)))

            for config in SecurityVisitor._ACCESS_CONTROL_CONFIGS:
                if (elem_name == config['attribute'] and au_type in config['au_type']
                    and parent_name in config['parents'] and not element.has_variable 
                    and elem_value.lower() not in config['values']
                    and config['values'] != [""]):
                    errors.append(Error('sec_access_control', element, file, repr(element)))
                    break
        return errors