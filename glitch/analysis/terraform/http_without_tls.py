from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, Variable


class TerraformHttpWithoutTls(TerraformSmellChecker):
    def check(self, element, file: str, code, au_type = None, parent_name = ""):
        errors = []
        if isinstance(element, AtomicUnit):
            if (element.type == "data.http"):
                url = self.check_required_attribute(element.attributes, [""], "url")
                if ("${" in url.value):
                    vars = url.value.split("${")
                    r = url.value.split("${")[1].split("}")[0]
                    for var in vars:
                        if "data" in var or "resource" in var:
                            r = var.split("}")[0]
                            break
                    type = r.split(".")[0]
                    if type in ["data", "resource"]:
                        resource_type = r.split(".")[1]
                        resource_name = r.split(".")[2]
                    else:
                        type = "resource"
                        resource_type = r.split(".")[0]
                        resource_name = r.split(".")[1]
                    if self.get_au(code, file, resource_name, type + "." + resource_type):
                        errors.append(Error('sec_https', url, file, repr(url)))

            for config in SecurityVisitor._HTTPS_CONFIGS:
                if (config["required"] == "yes" and element.type in config['au_type']
                    and not self.check_required_attribute(element.attributes, config["parents"], config['attribute'])):
                    errors.append(Error('sec_https', element, file, repr(element),
                        f"Suggestion: check for a required attribute with name '{config['msg']}'."))
                    
        elif isinstance(element, Attribute) or isinstance(element, Variable):
            for config in SecurityVisitor._HTTPS_CONFIGS:
                if (element.name == config["attribute"] and au_type in config["au_type"] 
                    and parent_name in config["parents"] and not element.has_variable 
                    and element.value.lower() not in config["values"]):
                    return [Error('sec_https', element, file, repr(element))]
        return errors