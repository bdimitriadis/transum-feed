---
title: Transum Feed
emoji: ⚡
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 5.20.0
app_file: src/transum_app.py
pinned: false
license: gpl-3.0
short_description: Summarizing and translating feed content
---

## Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference

# Transum Feed

Transum feed is an application used to summarize and translate the entries of a feed of choice.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

- What things you need to install on your system

```
* Python > 3.10.x

* The requirement packages found in the requirements.txt file via pip
```

## Deployment

### Local Development and Testing

To run the application locally for development and testing purposes, execute the following command in your terminal:

```bash
python transum_app.py
```

### Deployment on Hugging Face Spaces

To deploy the project on Hugging Face Spaces, follow these steps:

1. Create an account on [Hugging Face](https://huggingface.co) if you don’t already have one.

2. Refer to the official [Spaces Overview](https://huggingface.co/docs/hub/en/spaces-overview) documentation for detailed instructions on setting up and deploying your project.

### Deployment on Other Cloud Platforms

For deployment on other cloud or live systems, consult the documentation provided by your chosen service provider. Each platform may have specific requirements and steps for deploying Python-based applications.

> [!TIP] > **Hardware Recommendations**
>
> GPU Usage: It is highly recommended to use GPUs for deployment, especially for resource-intensive tasks like summarization. GPU acceleration significantly reduces processing time compared to CPUs.
>
> CPU Usage: While CPUs can be used for deployment, they may result in slower performance, particularly for computationally demanding processes.

> [!NOTE]
> On Hugging Face in order to use GPUs that might be available with your account (depends on your account type), you have to uncomment **_import spaces_** and **_@spaces.GPU_** lines in **_transum_app.py_** file.

## Built With

- [Python 3.10.12](http://www.python.org/) - Developing with the best programming language

## Authors

**Vlasios Dimitriadis** - _Initial work:_ [transum-feed](https://github.com/bdimitriadis/transum-feed/)
