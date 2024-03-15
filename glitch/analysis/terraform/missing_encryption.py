import re
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, Variable


class TerraformMissingEncryption(TerraformSmellChecker):
    def check(self, element, file: str, code, au_type = None, parent_name = ""):
        errors = []
        if isinstance(element, AtomicUnit):
            if (element.type == "resource.aws_s3_bucket"):
                expr = "\${aws_s3_bucket\." + f"{element.name}\."
                pattern = re.compile(rf"{expr}")
                r = self.get_associated_au(code, file, "resource.aws_s3_bucket_server_side_encryption_configuration", 
                    "bucket", pattern, [""])
                if not r:
                    errors.append(Error('sec_missing_encryption', element, file, repr(element), 
                        f"Suggestion: check for a required resource 'aws_s3_bucket_server_side_encryption_configuration' " + 
                            f"associated to an 'aws_s3_bucket' resource."))
            elif (element.type == "resource.aws_eks_cluster"):
                resources = self.check_required_attribute(element.attributes, ["encryption_config"], "resources[0]")
                if resources is not None:
                    i = 0
                    valid = False
                    while resources:
                        a = resources
                        if resources.value.lower() == "secrets":
                            valid = True
                            break
                        i += 1
                        resources = self.check_required_attribute(element.attributes, ["encryption_config"], f"resources[{i}]")
                    if not valid:
                        errors.append(Error('sec_missing_encryption', a, file, repr(a)))
                else:
                    errors.append(Error('sec_missing_encryption', element, file, repr(element), 
                        f"Suggestion: check for a required attribute with name 'encryption_config.resources'."))
            elif (element.type in ["resource.aws_instance", "resource.aws_launch_configuration"]):
                ebs_block_device = self.check_required_attribute(element.attributes, [""], "ebs_block_device")
                if ebs_block_device is not None:
                    encrypted = self.check_required_attribute(ebs_block_device.keyvalues, [""], "encrypted")
                    if not encrypted:
                        errors.append(Error('sec_missing_encryption', element, file, repr(element), 
                        f"Suggestion: check for a required attribute with name 'ebs_block_device.encrypted'."))
            elif (element.type == "resource.aws_ecs_task_definition"):
                volume = self.check_required_attribute(element.attributes, [""], "volume")
                if volume is not None:
                    efs_volume_config = self.check_required_attribute(volume.keyvalues, [""], "efs_volume_configuration")
                    if efs_volume_config is not None:
                        transit_encryption = self.check_required_attribute(efs_volume_config.keyvalues, [""], "transit_encryption")
                        if not transit_encryption:
                            errors.append(Error('sec_missing_encryption', element, file, repr(element), 
                            f"Suggestion: check for a required attribute with name" +
                                f"'volume.efs_volume_configuration.transit_encryption'."))

            for config in SecurityVisitor._MISSING_ENCRYPTION:
                if (config['required'] == "yes" and element.type in config['au_type']
                    and not self.check_required_attribute(element.attributes, config['parents'], config['attribute'])):
                    errors.append(Error('sec_missing_encryption', element, file, repr(element), 
                        f"Suggestion: check for a required attribute with name '{config['msg']}'."))
                    
        elif isinstance(element, Attribute) or isinstance(element, Variable):
            for config in SecurityVisitor._MISSING_ENCRYPTION:
                if (element.name == config['attribute'] and au_type in config['au_type']
                    and parent_name in config['parents'] and config['values'] != [""]):
                    if ("any_not_empty" in config['values'] and element.value.lower() == ""):
                        errors.append(Error('sec_missing_encryption', element, file, repr(element)))
                        break
                    elif ("any_not_empty" not in config['values'] and not element.has_variable 
                        and element.value.lower() not in config['values']):
                        errors.append(Error('sec_missing_encryption', element, file, repr(element)))
                        break

            for item in SecurityVisitor._CONFIGURATION_KEYWORDS:
                if item.lower() == element.name:
                    for config in SecurityVisitor._ENCRYPT_CONFIG:
                        if au_type in config['au_type']:
                            expr = config['keyword'].lower() + "\s*" + config['value'].lower()
                            pattern = re.compile(rf"{expr}")
                            if not re.search(pattern, element.value) and config['required'] == "yes":
                                errors.append(Error('sec_missing_encryption', element, file, repr(element)))
                                break
                            elif re.search(pattern, element.value) and config['required'] == "must_not_exist":
                                errors.append(Error('sec_missing_encryption', element, file, repr(element)))
                                break
        return errors