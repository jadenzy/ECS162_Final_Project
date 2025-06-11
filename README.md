## ECS162 Final Project - Group 13

### Group members:
  - JADEN YANG, University of California Davis, USA
  - CHEN-YU FAN, University of California Davis, USA
  - YUNFEI QUAN, University of California Davis, USA
  - NATHAN CASTELLON, University of California Davis, USA
  - HYUNHO SONG, University of California Davis, USA
  - YU-FAN CHEN, University of California Davis, USA

### Final Report: [Click to view the PDF file](ECS_162_final.pdf)

### Demo: [Click to view the demo](https://drive.google.com/file/d/106_byUtdIadEy_-PQdBztpBUo37dORDm/view?resourcekey)

### Running Instructions

- **Run Docker and localhost the frontend**  
  ```bash
  docker-compose -f docker-compose.dev.yml up --build 
  http://localhost:5173
  ```

## Important info: 
  - The login functions works as the following: 
    1. Redirect to dex 
    2. Vertify the info, and save the user info to the database 
    3. Redirect to frontend localhost 
    4. The frontend will call /api/user to check if any user has been save in the Database session, if so then render the username and logout 

  - The comment functions contains: 
    - Post: post will allow nested replies 
    - Delete: Each user can only delete its own commends, but if username == **'moderator'**, then can delete any comments. If delete a comment with replies, then the entier reply tree will be deleted at that level 
    - Get: get the comments for a article based on its own id 
    - Patch: Only the **moderator** can do this, which it to make a comment as █

  - The article functions contains:
    - Post: **Publisher** can post the new article, but need moderator's permission to approve 
    - Get: Get articles from New York Times or publisher posted
    - Delete: Only the **moderator** can delete articles

  - There are 4 preset users in config/dex: 
    1. username: admin
      - email: admin@hw3.com
      - password = "password"
     
    2. username: moderator, **moderator** is set as this one 
      - email: moderator@hw3.com
      - password = "mpassword" 
     
    3. username: user
      - email: user@hw3.com
      - password = "upassword"

    4. username: publisher
      - email: publisher@hw3.com
      - password = "password"
      
## Frontend Structure

### `/src`
- **`app.css`**
  - Redesign the entire page UI 

- **`App.svelte`**
  - Contains the all the frontend work 
  - Redesign the entire view, split the articles into three different sections based on the their length
  - Add light and dark mode
  - Redesign the header and footer
  - Add the publisher publisher article panel and button
  - Add the moderator approving panel for onhold articles
  - Add the displaying full article when onclick
  - Redesign the view of the comment sections and buttons

- **`CommentItem.svelte`**
  - The main components to render the comments for each articles 
  - Allow nested replies, but if deleting the parent comment, all the child comments will be deleteed 

## Backend Structure

### `app.py`
  - Add all the needed functions for MangoDB 
  - Login functions by using dex 
  - GET, POST, DELETE, PATCH apis for the comments 
  - Everything will save to the database including the articles and their corresponding articles 
  - Publisher POST article 
  - Moderator DELETE article and APPROVE article 
  - Fetch Approve articles for all users 
  - Get pending articles for moderator
  - Fetch Unapproved articles for publisher and moderator (pending will display)

  - Comment is an object contains    
    - "article_id"
    - "text"
    - "user": the user name 
    - "redacted_text": if the moderator do it or not 
    - "parent_id": if it contains a parent reply 

  - Article is an object contains 
    - "headline": the headline 
    - "abstract": the abstract 
    - "section_name": the section that the article belong to 
    - "body": the main content 
    - "byline": author of the article 
    - "multimedia": images of the article 
    - "approved": approve by moderator or not, all the NYT articles are default approved 

    - For publishing and fetching articles, the logic is as following: 
      - For the publishing: publisher publish a new article -> on hold for the moderator to approve -> moderator approve -> everyone can see it; if moderator not approve, it will be deleted. 
      - For fetching articles: include both fetch unapproved articles (article['approve'] = False) and fetch approve articles (article['approve'] = True), NYT articles are always article['approve'] = True. 
      - Fetch unapproved articles only for publisher and moderator, fetch approve articles for everyone. 
  


    

