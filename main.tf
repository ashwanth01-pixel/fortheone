provider "aws" {
  region                  = "us-east-1"
  shared_credentials_files = ["~/.aws/credentials"]
}
 
resource "aws_instance" "web" {
  ami           = "ami-04f59c565deeb2199"
  instance_type = "t2.medium"
  key_name      = "ashwanthramnv"
 
  user_data = file("./script.sh")
  tags = {
    Name = "ashwanthramnv1"
  }
}
