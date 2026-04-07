# ============================================
# 1. Base resources: Subscription, Resource group
# ============================================

resource "azurerm_resource_group" "rg_name" {
  name     = var.rg_name
  location = var.location
}

# ============================================
# 2. Communication resoruces: ACS
# ============================================

resource "azurerm_communication_service" "acs" {
  name                = "ACS-opti"
  resource_group_name = azurerm_resource_group.rg_name.name
  data_location       = "United States"


  tags = var.tags
}

# ============================================
# 2. Network settings: Virtual network, subnets, public ip, security group
# ============================================

resource "azurerm_virtual_network" "vnet" {
  name                = "vnet_resoruces"
  address_space       = ["192.168.10.0/26"]
  location            = azurerm_resource_group.rg_name.location
  resource_group_name = azurerm_resource_group.rg_name.name

  tags = var.tags

}

resource "azurerm_subnet" "subnet1" {
  name                 = "subnet_vm"
  resource_group_name  = azurerm_resource_group.rg_name.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["192.168.10.0/28"] # usable IPs: 192.168.10.1 - 192.168.10.14

  # service_endpoints = ["Microsoft.Storage"]

}


resource "azurerm_public_ip" "vm_public_ip" {
  name                = "PublicIp1"
  resource_group_name = azurerm_resource_group.rg_name.name
  location            = azurerm_resource_group.rg_name.location
  allocation_method   = "Dynamic" #The IP address isn't given to the resource at the time of creation when selecting dynamic. The IP is assigned when you associate the public IP address with a resource. The IP address is released when you stop, or delete the resource.

  lifecycle {
    create_before_destroy = true # Por recomendacion de la documentacion de terraform
  }
  tags = var.tags
}

resource "azurerm_network_security_group" "nsg" {
  name                = "vm-nsg"
  resource_group_name = azurerm_resource_group.rg_name.name
  location            = azurerm_resource_group.rg_name.location

  security_rule {
    name                    = "internetAccess"
    priority                = 200
    direction               = "Inbound"
    access                  = "Allow"
    protocol                = "Tcp"
    source_address_prefix   = "Internet" # acceso de internet a esta vm
    destination_port_ranges = ["80", "8080", "443"]
    source_port_range       = "*"
  }

  security_rule {
    name                    = "sshAccess"
    priority                = 100
    direction               = "Inbound"
    access                  = "Allow"
    protocol                = "Tcp"
    source_port_range       = "*"
    destination_port_range  = "22"
    source_address_prefixes = var.my_ip_adresses
  }

  tags = var.tags
}

resource "azurerm_network_interface" "nic_vm" {
  name                = "opti-nic"
  location            = azurerm_resource_group.rg_name.location
  resource_group_name = azurerm_resource_group.rg_name.name

  ip_configuration {
    name                          = "nic-connection"
    subnet_id                     = azurerm_subnet.subnet1.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.vm_public_ip.id
  }

  tags = var.tags
}

resource "azurerm_network_interface_security_group_association" "nic_sg" {
  network_interface_id      = azurerm_network_interface.nic_vm.id
  network_security_group_id = azurerm_network_security_group.nsg.id
}

# ============================================
# 3. Storage: FS, Volumes
# ============================================



# ============================================
# 4. Virtual Machine: VM, Disks
# ============================================

# resource "azurerm_linux_virtual_machine" "opti_vm" {
#   name                = "opti-linux-vm"
#   resource_group_name = azurerm_resource_group.rg_name.name
#   location            = azurerm_resource_group.rg_name.location

#   # El tamaño más pequeño y barato de Azure (aprox. $4 USD/mes)
#   size                  = "Standard_B2as"
#   admin_username        = "adminopti"
#   network_interface_ids = [azurerm_network_interface.nic_vm.id]

#   admin_ssh_key {
#     username   = "adminopti"
#     public_key = file(pathexpand(var.public_key_path))
#   }

#   os_disk {
#     caching = "ReadWrite"
#     # IMPORTANTE: Cambia a Standard_LRS (HDD) para ahorrar más
#     # Premium_LRS es más caro.
#     storage_account_type = "StandardSSD_LRS"
#     disk_size_gb         = 30 # El mínimo para Ubuntu suele ser 30GB
#   }

#   source_image_reference {
#     publisher = "Canonical"
#     offer     = "0001-com-ubuntu-server-jammy"
#     sku       = "22_04-lts"
#     version   = "latest"
#   }
# }

# resource "azurerm_managed_disk" "opti_disk" {
#   name                 = "optiDisk"
#   resource_group_name  = azurerm_resource_group.rg_name.name
#   location             = azurerm_resource_group.rg_name.location
#   storage_account_type = "StandardSSD_LRS"
#   create_option        = "Empty"
#   disk_size_gb         = "40"

#   tags = var.tags
# }

# resource "azurerm_virtual_machine_data_disk_attachment" "opti_attach_disk" {
#   managed_disk_id    = azurerm_managed_disk.opti_disk.id
#   virtual_machine_id = azurerm_linux_virtual_machine.opti_vm.id

#   lun     = 1 # Logical Unit Number. Needs to be unique within the VM
#   caching = "ReadWrite"
# }
