resource "azurerm_resource_group" "rg_name" {
  name     = var.rg_name
  location = var.location
}

resource "azurerm_communication_service" "acs" {
  name                = "ACS-opti"
  resource_group_name = azurerm_resource_group.rg_name.name
  data_location       = "United States"

  tags = {
    "createdBy" = "Terraform",
    "isModule"  = "false"
  }
}
