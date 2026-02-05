variable "subs_id" {
  description = "ID of the subscription"
  type        = string
}

variable "location" {
  description = "location/region"
  type        = string
  default     = "East US"
}

variable "rg_name" {
  description = "name of the RG"
  type        = string
  default     = "RG_Optinoc"
}

variable "tags" {
  description = "tags for resources"
  type        = map(string)
  default = {
    "createdBy" : "Terraform",
    "isModule" : "false",
  }
}

variable "my_ip_adresses" {
  description = "IP adresses to connect to vm by ssh"
  type        = set(string)
  default     = ["192.168.0.1"]

}

variable "public_key_path" {
  type = string
}
