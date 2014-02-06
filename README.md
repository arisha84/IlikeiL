# Introduction
## Purpose
iLike-IL is an application designed to elevate the level of awareness and understanding of the State
of Israel. All around the world public opinion is determined by the media, which often presents a one-sided picture. In many places Israel, despite its size and population, is considered to be the biggest threat to world peace.
iLike-IL is an advocacy application designed to allow users an easy way to search and comment on
articles related to Israel.
Combined with an aiding toolkit the user can easily find relevant tips and videos, and thus post a
more knowledgeable talkback for other readers to see.
Moreover- with simple modifications to the search criterions, the application can be used as a PR application, designed to find articles on any particular issues (i.e McDonalds, Toyota, etc.) and allow company representatives to comment on that issue.
Currently, there is a lot of interest in the application from different organizations that deals with
Israeli advocacy. Our main cooperation is with StandWithUS, one of the biggest organizations
in the field. We are in contact directly with the manger in Israel who promised us full support
publishing the site.

## Scope
The goal of this application is to allow an easy and convenient way to search articles which contain talk-backs, and aid the user to post knowledgeable comments.
Registered users can save and track history of their activities, including articles they commented on, marked as favorites and/or marked as relevant/irrelevant.
In addition- users, and especially preferred users and admins- can effect on the articles ranking and relevance with their ranking

# Architecture
## Overview
The application was designed so that it could easily be changed to be a different PR application- by simply changing the keywords used for the article searching and analysis, the application can allow searching of articles on about any subject, thus allowing company representatives to easily find and comment on negative articles on their company.
Backend

## Backend
The backend is responsible for processing and finally inserting new articles to the datastore. Using cron jobs (and task queues) we are scheduling our article "pipeline" which puts a new article through a series of checks (explained later). Afterwards, if qualified, the backend is responsible to add the article to the system. This includes, adding a newly discovered source to the DB, updating the cache and so on.
We also scheduled article recalculation process which updates the rank of the article which is described later.

## Frontend
Consists page handlers, templates, javascript and JQuery scripts. Responsible for authenticating the user, page rendering and processing user input. Also consists the admin interface that allows editing the system entities.

### Features
* Search and Analyze articles on Israel including talkback recognition, keywords analysis etc.
* Use a ranking algorithm to classify the articles based on their importance, and present the articles to the users based on their classification.
* The toolkit- help the user by presenting relevant tips and articles management buttons.
* Users support- allow users to register to the website using different accounts, and give preferred users with special capabilities.
* Monitoring- allow users to save information about articles- favorites, commented, relevant/irrelevant articles, as well as effect articles importance according to users actions.
* Keywords search- allow users to search for specific articles based on one or more keywords from the keywords database.
* Admin capabilities- allow admin users to manually add tips and keywords, manage sources and keywords priorities, and verify new (unverified) articles.
* Articles addition- allow users to manually add new articles easily using a special bookmarklet / favorites button.
* Language support- Spanish is also supported in addition to English, and other languages which are supported by google news can be easily added later.
* Facebook integration- Turn iLike-IL into a Facebook application.

# Implemented Technologies
iLike-IL is written in python, and designed in HTML over Google App engine.
Our application utilizes the following Google App Engine APIs:
* The Datastore
* Scheduled Tasks (Cron jobs)
* Memory caching - memcache
* Task queues
Additional technologies and APIs used in our application:
* YouTube Data API (for the YouTube feeds)
* Janrain API (for the multiple-platform login)
* Facebook API (for the application)
* JQuery Framework - for most of the Javascript in the system, especially for the client-side AJAX.
* JQuery UI - for most of our client-side UI features
* DateUtil - for easy parsing of dates (from manually-added articles)
* Google News RSS feeds – not an official API, but we use it anyway
* Google Analytics – monitoring users and interactions
iLikeIL - Project Documentation Page 15
* Google AppStats – profiling our app in detail
* BeautifulSoup – parsing html from source sites and Google News

