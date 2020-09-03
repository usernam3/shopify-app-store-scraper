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

While the dataset published on Kaggle is regularly updated, this repository allows keeping the local copy up to date independently of the released version.

Detailed dataset description can be found [here](https://www.kaggle.com/usernam3/shopify-app-store).

## How to use it

### Docker (recommended)

[Authenticate to GitHub Container Registry](https://docs.github.com/en/packages/getting-started-with-github-container-registry/migrating-to-github-container-registry-for-docker-images#authenticating-with-the-container-registry) (if not already)

```bash
docker login ghcr.io -u USERNAME -p TOKEN
```

Pull container

```bash
docker pull ghcr.io/usernam3/shopify-app-store-scraper
```

Run container

```bash
docker run -v `pwd`/output/:/app/output/ ghcr.io/usernam3/shopify-app-store-scraper
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
