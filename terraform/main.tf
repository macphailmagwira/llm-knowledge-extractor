terraform {
 required_providers {
   azurerm = {
     source  = "hashicorp/azurerm"
     version = "~> 3.0"
   }
 }
}

provider "azurerm" {
 features {}
}

variable "location" {
 description = "Azure region"
 type        = string
 default     = "East US"
}

variable "admin_username" {
 description = "Admin username for the VM"
 type        = string
 default     = "azureuser"
}

variable "admin_password" {
 description = "Admin password for the VM"
 type        = string
 sensitive   = true
}

# Resource Group
resource "azurerm_resource_group" "llm_extractor" {
 name     = "rg-llm-extractor"
 location = var.location
}

# Virtual Network
resource "azurerm_virtual_network" "llm_extractor" {
 name                = "vnet-llm-extractor"
 address_space       = ["10.0.0.0/16"]
 location            = azurerm_resource_group.llm_extractor.location
 resource_group_name = azurerm_resource_group.llm_extractor.name
}

# Subnet
resource "azurerm_subnet" "llm_extractor" {
 name                 = "subnet-llm-extractor"
 resource_group_name  = azurerm_resource_group.llm_extractor.name
 virtual_network_name = azurerm_virtual_network.llm_extractor.name
 address_prefixes     = ["10.0.1.0/24"]
}

# Network Security Group
resource "azurerm_network_security_group" "llm_extractor" {
 name                = "nsg-llm-extractor"
 location            = azurerm_resource_group.llm_extractor.location
 resource_group_name = azurerm_resource_group.llm_extractor.name

 security_rule {
   name                       = "SSH"
   priority                   = 1001
   direction                  = "Inbound"
   access                     = "Allow"
   protocol                   = "Tcp"
   source_port_range          = "*"
   destination_port_range     = "22"
   source_address_prefix      = "*"
   destination_address_prefix = "*"
 }

 security_rule {
   name                       = "HTTP"
   priority                   = 1002
   direction                  = "Inbound"
   access                     = "Allow"
   protocol                   = "Tcp"
   source_port_range          = "*"
   destination_port_range     = "11000"
   source_address_prefix      = "*"
   destination_address_prefix = "*"
 }
}

# Public IP
resource "azurerm_public_ip" "llm_extractor" {
 name                = "pip-llm-extractor"
 resource_group_name = azurerm_resource_group.llm_extractor.name
 location            = azurerm_resource_group.llm_extractor.location
 allocation_method   = "Static"
}

# Network Interface
resource "azurerm_network_interface" "llm_extractor" {
 name                = "nic-llm-extractor"
 location            = azurerm_resource_group.llm_extractor.location
 resource_group_name = azurerm_resource_group.llm_extractor.name

 ip_configuration {
   name                          = "internal"
   subnet_id                     = azurerm_subnet.llm_extractor.id
   private_ip_address_allocation = "Dynamic"
   public_ip_address_id          = azurerm_public_ip.llm_extractor.id
 }
}

# Associate Network Security Group to Network Interface
resource "azurerm_network_interface_security_group_association" "llm_extractor" {
 network_interface_id      = azurerm_network_interface.llm_extractor.id
 network_security_group_id = azurerm_network_security_group.llm_extractor.id
}

# Virtual Machine
resource "azurerm_linux_virtual_machine" "llm_extractor" {
 name                = "vm-llm-extractor"
 resource_group_name = azurerm_resource_group.llm_extractor.name
 location            = azurerm_resource_group.llm_extractor.location
 size                = "Standard_B2s"
 admin_username      = var.admin_username

 disable_password_authentication = false
 admin_password                  = var.admin_password

 network_interface_ids = [
   azurerm_network_interface.llm_extractor.id,
 ]

 os_disk {
   caching              = "ReadWrite"
   storage_account_type = "Premium_LRS"
 }

 source_image_reference {
   publisher = "Canonical"
   offer     = "0001-com-ubuntu-server-jammy"
   sku       = "22_04-lts-gen2"
   version   = "latest"
 }

 custom_data = base64encode(<<-EOF
             #!/bin/bash
             apt-get update
             apt-get install -y docker.io docker-compose-v2 git
             
             # Add user to docker group
             usermod -aG docker ${var.admin_username}
             
             # Start docker
             systemctl enable docker
             systemctl start docker
             
             # Clone and setup project (optional - remove if you prefer manual setup)
             # cd /home/${var.admin_username}
             # git clone <your-repo-url> llm-knowledge-extractor
             # chown -R ${var.admin_username}:${var.admin_username} llm-knowledge-extractor
             EOF
 )
}

# Outputs
output "public_ip_address" {
 value = azurerm_public_ip.llm_extractor.ip_address
}

output "ssh_command" {
 value = "ssh ${var.admin_username}@${azurerm_public_ip.llm_extractor.ip_address}"
}