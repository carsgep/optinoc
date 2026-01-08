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
