# CTX 100-Site Test Report

**Date**: 2026-03-30 19:57:49
**Tier**: fast (DOM rules only)
**Total sites**: 100

## Overall Results

  [+] pass    :  81 (81.0%)
  [~] partial :  13 (13.0%)
  [-] fail    :   4 (4.0%)
  [!] error   :   2 (2.0%)
  [?] unknown :   0 (0.0%)

## Per-Category Breakdown

| Category        |  Pass | Partial |  Fail | Error |  Avg Reduction |
|-----------------|-------|---------|-------|-------|----------------|
| ecommerce       |     7 |       2 |     0 |     1 |          79.6% |
| edge            |     4 |       4 |     2 |     0 |          62.4% |
| entertainment   |     7 |       2 |     1 |     0 |          99.6% |
| finance         |     8 |       1 |     1 |     0 |          95.4% |
| government      |     9 |       1 |     0 |     0 |          97.9% |
| marketing       |    10 |       0 |     0 |     0 |          99.5% |
| news            |     9 |       0 |     0 |     1 |          96.2% |
| search          |     8 |       2 |     0 |     0 |          92.5% |
| sports          |     9 |       1 |     0 |     0 |          90.7% |
| tech            |    10 |       0 |     0 |     0 |          95.5% |

## All Results

| Status   | Category     | Name                           |     HTML |      CTX |  Reduct | Para | Refs |     ms | Warnings/Error                           |
|----------|--------------|--------------------------------|----------|----------|---------|------|------|--------|------------------------------------------|
| pass     | ecommerce    | Amazon Product                 |    1631K |      41K |   97.5% |    4 |    1 |   4342 | too_many_skip                            |
| pass     | ecommerce    | Etsy                           |     225K |       1K |   99.2% |    2 |    0 |   2362 | no_refs, too_many_skip                   |
| pass     | ecommerce    | Newegg                         |     663K |       3K |   99.4% |    3 |    8 |   1013 |                                          |
| pass     | ecommerce    | Target                         |     359K |       1K |   99.7% |    1 |    0 |   2187 | no_refs, too_many_skip                   |
| pass     | ecommerce    | Walmart                        |     383K |      13K |   96.6% |   14 |    1 |   1074 |                                          |
| pass     | ecommerce    | Wayfair                        |     982K |       1K |   99.9% |    3 |    0 |   2992 | no_refs, too_many_skip                   |
| pass     | ecommerce    | Zappos                         |    1139K |       8K |   99.3% |    3 |    1 |   1540 |                                          |
| pass     | edge         | Arabic Wikipedia (RTL)         |       2K |     370B |   81.9% |    1 |    0 |    837 | no_refs                                  |
| pass     | edge         | Japanese Wikipedia             |       2K |     321B |   84.3% |    1 |    0 |    819 | no_refs                                  |
| pass     | edge         | Wikipedia: LLM (long page)     |       2K |     305B |   85.1% |    1 |    0 |    657 | no_refs                                  |
| pass     | edge         | XML feed (non-HTML)            |     522B |     242B |   53.6% |    1 |    0 |    973 | no_refs                                  |
| pass     | entertainment | Billboard Hot 100              |    3017K |       1K |  100.0% |    2 |    0 |   1969 | no_refs, too_many_skip                   |
| pass     | entertainment | Goodreads Book                 |     734K |      10K |   98.6% |    1 |    0 |   3513 | no_refs, too_many_skip                   |
| pass     | entertainment | Letterboxd Film                |     312K |       2K |   99.1% |    1 |    0 |    858 | no_refs, too_many_skip                   |
| pass     | entertainment | Metacritic                     |    1495K |     866B |   99.9% |    1 |    0 |   2263 | no_refs, too_many_skip                   |
| pass     | entertainment | Rotten Tomatoes                |     199K |     967B |   99.5% |    1 |    0 |   1086 | no_refs, too_many_skip                   |
| pass     | entertainment | Variety                        |     712K |       1K |   99.8% |    1 |    0 |   2867 | no_refs, too_many_skip                   |
| pass     | entertainment | YouTube Video                  |    1382K |     643B |  100.0% |    1 |    0 |   1954 | no_refs                                  |
| pass     | finance      | Bloomberg                      |      13K |     351B |   97.5% |    1 |    0 |   1177 | no_refs                                  |
| pass     | finance      | CNBC                           |    1236K |     804B |   99.9% |    1 |    0 |   1178 | no_refs, too_many_skip                   |
| pass     | finance      | Investopedia                   |     572K |      14K |   97.5% |    4 |    1 |   1471 | too_many_skip                            |
| pass     | finance      | Morningstar                    |       0B |    1016B |       - |    1 |    0 |   1660 | no_refs, too_many_skip                   |
| pass     | finance      | Motley Fool                    |     329K |       1K |   99.7% |    2 |    1 |    952 |                                          |
| pass     | finance      | Seeking Alpha                  |    1106K |       1K |   99.9% |    4 |    1 |   1233 | too_many_skip                            |
| pass     | finance      | WSJ                            |     767B |     240B |   68.7% |    1 |    0 |    742 | no_refs                                  |
| pass     | finance      | Yahoo Finance: AAPL            |    2650K |       2K |   99.9% |    1 |    0 |   1658 | no_refs, too_many_skip                   |
| pass     | government   | CDC                            |      58K |       1K |   97.2% |    1 |    0 |    595 | no_refs, too_many_skip                   |
| pass     | government   | Congress.gov                   |       4K |     263B |   94.3% |    1 |    0 |    367 | no_refs                                  |
| pass     | government   | Data.gov                       |     118K |     878B |   99.3% |    1 |    0 |    476 | no_refs, too_many_skip                   |
| pass     | government   | IRS                            |     100K |       2K |   97.8% |    5 |    1 |    447 |                                          |
| pass     | government   | NASA                           |     286K |       1K |   99.6% |    2 |    0 |    828 | no_refs                                  |
| pass     | government   | NIH                            |      58K |       1K |   97.7% |    1 |    0 |   1063 | no_refs, too_many_skip                   |
| pass     | government   | USA.gov                        |      46K |       1K |   97.1% |    1 |    0 |    729 | no_refs, too_many_skip                   |
| pass     | government   | WHO                            |     128K |     607B |   99.5% |    1 |    0 |    731 | no_refs, too_many_skip                   |
| pass     | government   | White House                    |     255K |       2K |   98.9% |    4 |    0 |    938 | no_refs, too_many_skip                   |
| pass     | marketing    | Buffer                         |     352K |     978B |   99.7% |    2 |    0 |    707 | no_refs                                  |
| pass     | marketing    | Canva                          |     372K |     716B |   99.8% |    1 |    0 |   1199 | no_refs, too_many_skip                   |
| pass     | marketing    | HubSpot Blog                   |     344K |       2K |   99.4% |    2 |    2 |   1259 | too_many_skip                            |
| pass     | marketing    | Mailchimp                      |     431K |       2K |   99.4% |    1 |    1 |    715 | too_many_skip                            |
| pass     | marketing    | Moz                            |     164K |       1K |   99.4% |    1 |    0 |    813 | no_refs, too_many_skip                   |
| pass     | marketing    | Neil Patel                     |     148K |       1K |   99.2% |    2 |    0 |    602 | no_refs                                  |
| pass     | marketing    | Salesforce                     |     552K |       1K |   99.8% |    1 |    0 |   1583 | no_refs, too_many_skip                   |
| pass     | marketing    | Semrush                        |     157K |       1K |   98.9% |    7 |    0 |   1051 | no_refs                                  |
| pass     | marketing    | Shopify Blog                   |     494K |       1K |   99.7% |    2 |    0 |    842 | no_refs, too_many_skip                   |
| pass     | marketing    | Wix                            |    2233K |       1K |   99.9% |    2 |    1 |   1696 |                                          |
| pass     | news         | ABC News                       |     680K |     712B |   99.9% |    1 |    0 |   5595 | no_refs, too_many_skip                   |
| pass     | news         | AP News                        |    1194K |       1K |   99.8% |    3 |    0 |   2196 | no_refs, too_many_skip                   |
| pass     | news         | Al Jazeera                     |     395K |     861B |   99.8% |    1 |    0 |    453 | no_refs, too_many_skip                   |
| pass     | news         | BBC News                       |     325K |     971B |   99.7% |    1 |    0 |    944 | no_refs, too_many_skip                   |
| pass     | news         | CNN                            |    4837K |       2K |   99.9% |    1 |    0 |   1528 | no_refs, too_many_skip                   |
| pass     | news         | NPR                            |     684K |       1K |   99.8% |    1 |    0 |    803 | no_refs, too_many_skip                   |
| pass     | news         | NY Times                       |    1264K |       1K |   99.9% |    1 |    0 |   2342 | no_refs, too_many_skip                   |
| pass     | news         | Reuters                        |     771B |     252B |   67.3% |    1 |    0 |    953 | no_refs                                  |
| pass     | news         | The Guardian                   |    1252K |       1K |   99.9% |    1 |    0 |   1676 | no_refs, too_many_skip                   |
| pass     | search       | Bing Search                    |     112K |     636B |   99.4% |    2 |    0 |   1912 | no_refs                                  |
| pass     | search       | Craigslist                     |      59K |     811B |   98.7% |    2 |    0 |   6413 | no_refs, too_many_skip                   |
| pass     | search       | DuckDuckGo                     |      23K |     341B |   98.6% |    3 |    0 |   1709 | no_refs                                  |
| pass     | search       | Google Search                  |      85K |     231B |   99.7% |    2 |    0 |   2239 | no_refs                                  |
| pass     | search       | Product Hunt                   |     981K |      15K |   98.4% |   92 |    1 |    743 |                                          |
| pass     | search       | Reddit r/programming           |     511K |       1K |   99.8% |    4 |    1 |   1699 |                                          |
| pass     | search       | Stack Overflow                 |     427K |       2K |   99.4% |    2 |    0 |   1172 | no_refs, too_many_skip                   |
| pass     | search       | Wikipedia Main                 |       2K |     294B |   85.7% |    1 |    0 |   1519 | no_refs                                  |
| pass     | sports       | BBC Sport                      |     617K |     762B |   99.9% |    1 |    0 |   1294 | no_refs, too_many_skip                   |
| pass     | sports       | Bleacher Report                |    4515K |      37K |   99.2% |    1 |    0 |   3208 | no_refs, too_many_skip                   |
| pass     | sports       | CBS Sports                     |     757K |     778B |   99.9% |    1 |    0 |   2231 | no_refs, too_many_skip                   |
| pass     | sports       | ESPN                           |     233K |     743B |   99.7% |    1 |    0 |   1946 | no_refs, too_many_skip                   |
| pass     | sports       | MLB.com                        |    1794K |       1K |   99.9% |    1 |    1 |   3241 | too_many_skip                            |
| pass     | sports       | NBA.com                        |     434K |      27K |   93.7% |   38 |    5 |   3828 |                                          |
| pass     | sports       | NFL.com                        |    3774K |     683B |  100.0% |    1 |    0 |   2772 | no_refs, too_many_skip                   |
| pass     | sports       | Sports Illustrated             |    1788K |       1K |   99.9% |    1 |    0 |   3539 | no_refs, too_many_skip                   |
| pass     | sports       | Yahoo Sports                   |    1933K |       1K |   99.9% |    1 |    0 |   4096 | no_refs, too_many_skip                   |
| pass     | tech         | Ars Technica                   |     391K |       1K |   99.5% |    2 |    0 |   1405 | no_refs, too_many_skip                   |
| pass     | tech         | Go Docs                        |      46K |       9K |   80.5% |   40 |    2 |    717 |                                          |
| pass     | tech         | MDN Web Docs                   |     173K |       6K |   96.4% |    3 |   25 |   1355 | too_many_skip                            |
| pass     | tech         | Python Docs                    |      36K |       4K |   88.8% |    9 |    4 |    314 |                                          |
| pass     | tech         | React Docs                     |     266K |     981B |   99.6% |    1 |    0 |    866 | no_refs, too_many_skip                   |
| pass     | tech         | Rust Book                      |      21K |       1K |   91.9% |    2 |    2 |    935 |                                          |
| pass     | tech         | TechCrunch                     |     412K |       1K |   99.6% |    1 |    0 |    619 | no_refs, too_many_skip                   |
| pass     | tech         | The Verge                      |     901K |       1K |   99.8% |    1 |    0 |    931 | no_refs, too_many_skip                   |
| pass     | tech         | TypeScript Docs                |     166K |       1K |   99.3% |    9 |    0 |    543 | no_refs                                  |
| pass     | tech         | Wired                          |    1351K |       1K |   99.9% |    1 |    0 |   1393 | no_refs, too_many_skip                   |
| partial  | ecommerce    | Home Depot                     |     371B |     313B |   15.6% |    2 |    0 |    416 | no_refs, low_reduction                   |
| partial  | ecommerce    | eBay                           |     376B |     343B |    8.8% |    2 |    0 |  35439 | no_refs, low_reduction                   |
| partial  | edge         | Slow page (25s, should timeout) |     354B |     582B |  -64.4% |    1 |    0 |  20902 | no_title, no_sections, no_refs           |
| partial  | edge         | Triple redirect                |     303B |     535B |  -76.6% |    1 |    0 |   1463 | no_title, no_sections, no_refs           |
| partial  | edge         | example.com (minimal)          |     528B |     354B |   33.0% |    2 |    1 |    589 | low_reduction                            |
| partial  | edge         | httpbin HTML (Moby Dick)       |       3K |       3K |    0.3% |    1 |    0 |   1023 | no_refs, low_reduction                   |
| partial  | entertainment | Spotify Artist                 |     103K |     184B |   99.8% |    0 |    0 |    923 | no_paragraphs, no_refs                   |
| partial  | entertainment | Twitch                         |     183K |     245B |   99.9% |    0 |    0 |    709 | no_paragraphs, no_refs                   |
| partial  | finance      | MarketWatch                    |     775B |     931B |  -20.1% |    4 |    0 |   1038 | no_refs, too_many_skip, low_reduction    |
| partial  | government   | NOAA                           |     919B |       1K |  -30.8% |    1 |    0 |    480 | no_refs, too_many_skip, low_reduction    |
| partial  | search       | GitHub Repo                    |     320K |       8K |   97.4% |    0 |    0 |   2224 | no_paragraphs, no_refs                   |
| partial  | search       | Hacker News                    |      34K |      17K |   47.9% |    1 |    7 |   1214 | low_reduction                            |
| partial  | sports       | ESPNcricinfo                   |     374B |     320B |   14.4% |    2 |    0 |   2991 | no_refs, low_reduction                   |
| fail     | edge         | 404 page                       |       0B |     115B |       - |    0 |    0 |    984 | no_title, no_paragraphs, no_sections     |
| fail     | edge         | PNG image (non-HTML)           |       7K |     138B |   98.3% |    0 |    0 |   1106 | no_title, no_paragraphs, no_sections     |
| fail     | entertainment | IMDb: Inception                |       0B |     107B |       - |    0 |    0 |    486 | no_title, no_paragraphs, no_sections     |
| fail     | finance      | Google Finance                 |    1284K |     143B |  100.0% |    0 |    0 |   2479 | no_title, no_paragraphs, no_sections     |
| error    | ecommerce    | Best Buy                       |       0B |       0B |       - |    0 |    0 |  41441 | Timeout (20s)                            |
| error    | news         | Washington Post                |       0B |       0B |       - |    0 |    0 |  40177 | Timeout (20s)                            |

## Errors (Detail)

### Best Buy (ecommerce)
- **URL**: https://www.bestbuy.com
- **Error**: Timeout (20s)

### Washington Post (news)
- **URL**: https://www.washingtonpost.com
- **Error**: Timeout (20s)

## Failures (Detail)

### 404 page (edge)
- **URL**: https://httpbin.org/status/404
- **Warnings**: no_title, no_paragraphs, no_sections, no_refs
- **CTX bytes**: 115
- **Paragraphs**: 0, Sections: 0
- **Preview**:
```
§doc.ctx_v1.0 url=https://httpbin.org/status/404 †type=error

§error type=fetch-failed
  †detail="HTTP 404"


```

### PNG image (non-HTML) (edge)
- **URL**: https://httpbin.org/image/png
- **Warnings**: no_title, no_paragraphs, no_sections, no_refs
- **CTX bytes**: 138
- **Paragraphs**: 0, Sections: 0
- **Preview**:
```
§doc.ctx_v1.0 url=https://httpbin.org/image/png †type=error

§error type=fetch-failed
  †detail="Non-HTML content-type: image/png"


```

### IMDb: Inception (entertainment)
- **URL**: https://www.imdb.com/title/tt1375666/
- **Warnings**: no_title, no_paragraphs, no_sections, no_refs, empty_content
- **CTX bytes**: 107
- **Paragraphs**: 0, Sections: 0
- **Preview**:
```
§doc.ctx_v1.0 url=https://www.imdb.com/title/tt1375666/ †type=reference †lang=en

§content.reference

```

### Google Finance (finance)
- **URL**: https://www.google.com/finance/quote/AAPL:NASDAQ
- **Warnings**: no_title, no_paragraphs, no_sections, no_refs
- **CTX bytes**: 143
- **Paragraphs**: 0, Sections: 0
- **Preview**:
```
§doc.ctx_v1.0 url=https://www.google.com/finance/quote/AAPL:NASDAQ †type=error

§error type=fetch-failed
  †detail="Too many redirects"


```

## Warning Frequency

- **no_refs**: 77 sites
- **too_many_skip**: 53 sites
- **low_reduction**: 10 sites
- **no_paragraphs**: 7 sites
- **no_title**: 6 sites
- **no_sections**: 6 sites
- **negative_reduction**: 4 sites
- **empty_content**: 1 sites

## Recommended Fixes (Auto-Generated)

- **no_refs** (77 sites): Annotator: Broaden link detection — check `<li>`, `<span>`, `<div>` containers, not just `<p>`
- **too_many_skip** (53 sites): Extractor: Cap skip blocks at 5 per document, merge duplicates
- **low_reduction** (10 sites): Pipeline: Investigate pages where CTX is >50% of HTML — likely minimal-markup pages or text-heavy content
- **no_paragraphs** (7 sites): Extractor: Broaden paragraph detection beyond `<p>` tags (some sites use `<div>`, `<span>`, `<article>` for body text)
- **no_title** (6 sites): Extractor: Fall back to `<h1>` text or URL-derived title when `<title>` and OG tags are missing
- **no_sections** (6 sites): Annotator: Generate a synthetic `§1` from page title when no headings are found
- **negative_reduction** (4 sites): Pipeline: CTX output should never exceed HTML input — check for extraction bloat or repeated content
- **empty_content** (1 sites): Extractor: When readability produces empty content, fall back to full `<body>` text extraction

### Error Types
- **Timeout (20s)**: 2 sites

---
*Generated by CTX test suite v1.0*