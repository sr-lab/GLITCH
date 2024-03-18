import re
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute


class TerraformReplication(TerraformSmellChecker):
    def check(self, element, file: str):
        errors = []
        if isinstance(element, AtomicUnit):
            if (element.type == "resource.aws_s3_bucket"):
                expr = "\${aws_s3_bucket\." + f"{element.name}\."
                pattern = re.compile(rf"{expr}")
                if not self.get_associated_au(file, "resource.aws_s3_bucket_replication_configuration", 
                    "bucket", pattern, [""]):
                    errors.append(Error('sec_replication', element, file, repr(element), 
                        f"Suggestion: check for a required resource 'aws_s3_bucket_replication_configuration' " + 
                            f"associated to an 'aws_s3_bucket' resource."))

            for config in SecurityVisitor._REPLICATION:
                if (config['required'] == "yes" and element.type in config['au_type'] 
                    and not self.check_required_attribute(element.attributes, config['parents'], config['attribute'])):
                    errors.append(Error('sec_replication', element, file, repr(element), 
                        f"Suggestion: check for a required attribute with name '{config['msg']}'."))
        
            def check_attribute(attribute: Attribute, parent_name: str):
                for config in SecurityVisitor._REPLICATION:
                    if (attribute.name == config['attribute'] and element.type in config['au_type']
                        and parent_name in config['parents'] and config['values'] != [""]
                        and not attribute.has_variable and attribute.value.lower() not in config['values']):
                        errors.append(Error('sec_replication', attribute, file, repr(attribute)))
                        break
                
                for child in attribute.keyvalues:
                    check_attribute(child, attribute.name)

            for attribute in element.attributes:
                check_attribute(attribute, "")

        return errors