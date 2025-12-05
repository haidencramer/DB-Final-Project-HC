import yaml

# Load the YAML file
with open('enivonment.yml', 'r') as file:
    config_data = yaml.safe_load(file)

# Modify the data
config_data['setting_name'] = 'new_value'
config_data['another_list'].append('new_item')

# Save the modified data back to the YAML file
with open('config.yaml', 'w') as file:
    yaml.dump(config_data, file, default_flow_style=False)