# Shopify App Store scraper

## About

Here you can find the code which scrapes and saves data from the [Shopify App Store](https://apps.shopify.com/).

The scraper is used to collect [Shopify app store dataset on Kaggle](https://www.kaggle.com/usernam3/shopify-app-store) and includes these files:
- `apps`
- `apps_categories`
- `categories`
- `key_benefits`
- `pricing_plan_features`
- `pricing_plans`
- `reviews`

Even though the published dataset is regularly updated, this repository allows keeping the local copy up to date independently of the released version.

Detailed dataset description can be found [here](https://www.kaggle.com/usernam3/shopify-app-store).

## How to use it

### Docker (recommended)

[Authenticate to Github Packages](https://help.github.com/en/github/managing-packages-with-github-packages/configuring-docker-for-use-with-github-packages#authenticating-to-github-packages) (if not already)

```bash
docker login docker.pkg.github.com -u USERNAME -p TOKEN
```

Pull container

```bash
docker pull docker.pkg.github.com/usernam3/shopify-app-store-scraper/shopify-app-store-scraper:v1
```

Run container

```bash
docker run -v `pwd`/output/:/app/output/ docker.pkg.github.com/usernam3/shopify-app-store-scraper/shopify-app-store-scraper:v1
```

After container finished the execution check the `output` folder (in current directory)

```bash
ls -la output/
```

### Python

Install requirements

```bash
pip install -r requirements.txt
``` 

Run scraper

```bash
scrapy crawl app_store
``` 
 
After container finished the execution check the `output` folder (in current directory)

```bash
ls -la output/
```

---

Please don't hesitate to open issues or PRs at any time if you need help with anything.