import re
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, Variable


class TerraformReplication(TerraformSmellChecker):
    def check(self, element, file: str, code, au_type = None, parent_name = ""):
        errors = []
        if isinstance(element, AtomicUnit):
            if (element.type == "resource.aws_s3_bucket"):
                expr = "\${aws_s3_bucket\." + f"{element.name}\."
                pattern = re.compile(rf"{expr}")
                if not self.get_associated_au(code, file, "resource.aws_s3_bucket_replication_configuration", 
                    "bucket", pattern, [""]):
                    errors.append(Error('sec_replication', element, file, repr(element), 
                        f"Suggestion: check for a required resource 'aws_s3_bucket_replication_configuration' " + 
                            f"associated to an 'aws_s3_bucket' resource."))

            for config in SecurityVisitor._REPLICATION:
                if (config['required'] == "yes" and element.type in config['au_type'] 
                    and not self.check_required_attribute(element.attributes, config['parents'], config['attribute'])):
                    errors.append(Error('sec_replication', element, file, repr(element), 
                        f"Suggestion: check for a required attribute with name '{config['msg']}'."))
        
        elif isinstance(element, Attribute) or isinstance(element, Variable):
            for config in SecurityVisitor._REPLICATION:
                if (element.name == config['attribute'] and au_type in config['au_type']
                    and parent_name in config['parents'] and config['values'] != [""]
                    and not element.has_variable and element.value.lower() not in config['values']):
                    return [Error('sec_replication', element, file, repr(element))]
        return errors