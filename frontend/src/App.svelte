<script>
  import { onMount } from 'svelte';
  import { fetchArticles } from './lib/api.js';
  import CommentItem from './CommentItem.svelte';

  export let today = '';
  export let menuOpen = false;

  let articles = [];
  let fetchError = false;
  let commentPanelOpen = false;
  let selectedArticle = null;
  let comments = [];
  let newCommentText = '';
  let user = null;
  let currentSection = 'Local';

  let fallbackData = {
    leadStory: {
      title: "Global Climate Summit Reaches Historic Agreement on Carbon Reduction",
      subtitle: "World leaders commit to ambitious new targets as scientists warn of critical tipping points",
      byline: "By Sarah Johnson and Michael Chen",
      excerpt: "In a groundbreaking development at the Global Climate Summit in Geneva, representatives from 195 nations reached a comprehensive agreement on carbon reduction targets that experts are calling the most ambitious climate accord since the Paris Agreement.",
      web_url: "#",
      multimedia: null
    },
    secondaryStories: [
      {
        title: "Tech Innovation Drives Economic Growth in Q2",
        byline: "By Alexandra Rodriguez",
        excerpt: "Artificial intelligence and renewable energy sectors showed remarkable growth this quarter, with tech stocks reaching new highs.",
        web_url: "#"
      },
      {
        title: "Archaeological Discovery Rewrites Ancient History",
        byline: "By Dr. James Thompson",
        excerpt: "A team of archaeologists in Peru has uncovered evidence of a previously unknown civilization that predates the Inca Empire by over 1,000 years.",
        web_url: "#"
      }
    ]
  };

  function toggleMenu() {
    menuOpen = !menuOpen;
  }

  function handleLogin() {
    window.location.href = '/login';
  }

  function closeComments() {
    commentPanelOpen = false;
    selectedArticle = null;
    comments = [];
  }

  async function openComments(article) {
    selectedArticle = article;
    commentPanelOpen = true;
    await fetchComments(article._id);
  }

  async function fetchComments(articleId) {
    try {
      const res = await fetch(`/api/comments?article_id=${articleId}`);
      comments = await res.json();
    } catch (e) {
      console.error('Failed to fetch comments:', e);
      comments = [];
    }
  }

  async function postComment() {
    if (!newCommentText.trim()) return;
    try {
      await fetch('/api/comments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          article_id: selectedArticle._id, 
          text: newCommentText, 
          parent_id: replyTo 
        }),
      });
      newCommentText = '';
      replyTo = null;
      await fetchComments(selectedArticle._id);
    } catch (e) {
      console.error('Failed to post comment:', e);
    }
  }

  async function deleteComment(id) {
    try {
      await fetch(`/api/comments?id=${id}`, { method: 'DELETE' });
      await fetchComments(selectedArticle._id);
    } catch (e) {
      console.error('Failed to delete comment:', e);
    }
  }

  async function redactComment(id, text) {
    try {
      await fetch('/api/comments', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, text }),
      });
      await fetchComments(selectedArticle._id);
    } catch (e) {
      console.error('Failed to redact comment:', e);
    }
  }

  let replyTo = null;
  function replyToComment(commentId) {
    replyTo = commentId;
    newCommentText = `@ `;
  }
  
  function getReplies(parentId) {
    return comments.filter(c => c.parent_id === parentId);
  }

  async function loadSection(section) {
    currentSection = section;
    menuOpen = false; 
    
    try {
      const result = await fetchArticles(section);
      articles = result.articles;
      fetchError = result.fetchError;
    } catch (e) {
      console.error('Failed to load section:', e);
      fetchError = true;
    }
  }

  $: leadStory = articles.length > 0 ? articles[0] : fallbackData.leadStory;
  
  $: secondaryStories = articles.length > 1 ? articles.slice(1, 5) : fallbackData.secondaryStories;
  
  $: sidebarStories = articles.length > 5 ? articles.slice(5, 8) : [];

  onMount(async () => {
    today = new Date().toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });

    try {
      const res = await fetch('/api/user', { credentials: 'include' });
      user = await res.json();
    } catch (e) {
      user = null;
    }

    await loadSection('Local');
  });
</script>

<svelte:head>
  <title>The New York Times Final Project</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</svelte:head>

<header class="header">
  <div class="header-top">
    <div class="date">{today}</div>
    <button class="logo" on:click={() => loadSection('Local')}>The New York Times</button>
    <div class="user-info">
      {#if user && !user.error}
        Welcome, {user?.name} | <a href="/logout">Logout</a>
        {#if user.name === 'publisher'}
          <span class="publisher-badge">Publish Article</span>
        {/if}
      {:else}
        <button class="login-btn" on:click={handleLogin}>Login</button>
      {/if}
    </div>
    <button class="hamburger {menuOpen ? 'open' : ''}" on:click={toggleMenu}>☰</button>
  </div>
</header>

<nav class="nav {menuOpen ? 'open' : ''}">
  <div class="nav-container">
    <ul>
      <li><a href="#" on:click|preventDefault={() => loadSection('Local')} class:active={currentSection === 'Local'}>Local</a></li>
      <li><a href="#" on:click|preventDefault={() => loadSection('U.S.')} class:active={currentSection === 'U.S.'}>U.S.</a></li>
      <li><a href="#" on:click|preventDefault={() => loadSection('World')} class:active={currentSection === 'World'}>World</a></li>
      <li><a href="#" on:click|preventDefault={() => loadSection('Climate')} class:active={currentSection === 'Climate'}>Climate</a></li>
      <li><a href="#" on:click|preventDefault={() => loadSection('Arts')} class:active={currentSection === 'Arts'}>Arts</a></li>
      <li><a href="#" on:click|preventDefault={() => loadSection('Opinion')} class:active={currentSection === 'Opinion'}>Opinion</a></li>
    </ul>
  </div>
</nav>

{#if fetchError}
  <div class="error-message">
    <p>Failed to load news. Please try again later.</p>
    <button on:click={() => loadSection(currentSection)}>Retry</button>
  </div>
{:else if articles.length === 0}
  <div class="loading">
    <p>Loading latest news...</p>
  </div>
{:else}
  <div class="container {commentPanelOpen ? 'blurred' : ''}">
    <main class="main-content">
      <article class="lead-story">
        {#if leadStory.multimedia}
          <img src={leadStory.multimedia.url || leadStory.multimedia.default?.url} alt="Lead story image" class="lead-image" />
        {/if}
        <h1>
          <a href={leadStory.web_url} target="_blank" rel="noopener noreferrer">
            {leadStory.headline?.main || leadStory.title}
          </a>
        </h1>
        {#if leadStory.subtitle}
          <p class="subtitle">{leadStory.subtitle}</p>
        {/if}
        <p class="byline">{leadStory.byline?.original || leadStory.byline}</p>
        <p class="excerpt">{leadStory.abstract || leadStory.excerpt}</p>
        {#if leadStory._id}
          <button class="comment-button" on:click={() => openComments(leadStory)}>💬 Comment</button>
        {/if}
      </article>

      <section class="secondary-stories">
        {#each secondaryStories as story}
          <article class="story">
            {#if story.multimedia}
              <img src={story.multimedia.url || story.multimedia.default?.url} alt="Article image" class="story-image" />
            {/if}
            <h2>
              <a href={story.web_url} target="_blank" rel="noopener noreferrer">
                {story.headline?.main || story.title}
              </a>
            </h2>
            <p class="byline">{story.byline?.original || story.byline}</p>
            <p class="excerpt">{story.abstract || story.excerpt}</p>
            {#if story._id}
              <button class="comment-button" on:click={() => openComments(story)}>💬 Comment</button>
            {/if}
          </article>
        {/each}
      </section>

      {#if currentSection === 'Opinion' && articles.length > 0}
        <section class="opinion-section">
          <h3>Opinion</h3>
          <article class="story">
            <h2>
              <a href={articles[0].web_url} target="_blank" rel="noopener noreferrer">
                {articles[0].headline?.main || articles[0].title}
              </a>
            </h2>
            <p class="byline">{articles[0].byline?.original || articles[0].byline}</p>
            <p class="excerpt">{articles[0].abstract || articles[0].excerpt}</p>
            {#if articles[0]._id}
              <button class="comment-button" on:click={() => openComments(articles[0])}>💬 Comment</button>
            {/if}
          </article>
        </section>
      {/if}
    </main>

    <aside class="sidebar">
      <section class="sidebar-section">
        <h3>Most Popular</h3>
        {#each sidebarStories as story}
          <article class="sidebar-story">
            <h4>
              <a href={story.web_url} target="_blank" rel="noopener noreferrer">
                {story.headline?.main || story.title}
              </a>
            </h4>
            <p class="byline">{story.byline?.original || story.byline}</p>
            <p class="excerpt">{(story.abstract || story.excerpt || '').substring(0, 100)}...</p>
            {#if story._id}
              <button class="comment-button small" on:click={() => openComments(story)}>💬</button>
            {/if}
          </article>
        {/each}
      </section>
    </aside>
  </div>
{/if}

<footer class="footer">
  <div class="footer-content">
    <div class="footer-section">
      <h4>News</h4>
      <ul>
        <li><a href="#" on:click|preventDefault={() => loadSection('World')}>World</a></li>
        <li><a href="#" on:click|preventDefault={() => loadSection('U.S.')}>U.S.</a></li>
        <li><a href="#" on:click|preventDefault={() => loadSection('Local')}>Local</a></li>
        <li><a href="#" on:click|preventDefault={() => loadSection('Climate')}>Climate</a></li>
      </ul>
    </div>
    <div class="footer-section">
      <h4>Opinion</h4>
      <ul>
        <li><a href="#" on:click|preventDefault={() => loadSection('Opinion')}>Opinion</a></li>
        <li><a href="#">Editorials</a></li>
        <li><a href="#">Op-Ed Columnists</a></li>
        <li><a href="#">Letters</a></li>
      </ul>
    </div>
    <div class="footer-section">
      <h4>Arts</h4>
      <ul>
        <li><a href="#" on:click|preventDefault={() => loadSection('Arts')}>Arts</a></li>
        <li><a href="#">Books</a></li>
        <li><a href="#">Movies</a></li>
        <li><a href="#">Theater</a></li>
      </ul>
    </div>
    <div class="footer-section">
      <p>&copy;2025 ECS 162 HW1. &copy;Team 13. All rights reserved.</p>
    </div>
  </div>
</footer>

{#if commentPanelOpen}
  <aside class="comment-panel">
    <button class="close-panel" on:click={closeComments}>✖</button>
    <h3>Comments</h3>
    <p><strong>{selectedArticle.headline?.main || selectedArticle.title}</strong></p>

    <div class="comment-list">
      {#each comments.filter(c => !c.parent_id) as rootComment}
        <CommentItem
          comment={rootComment}
          replies={getReplies(rootComment._id)}
          {user}
          onReply={replyToComment}
          onDelete={deleteComment}
          onRedact={redactComment}
          {getReplies}
        />
      {/each}
    </div>

    {#if user && !user.error}
      <div class="comment-form">
        <textarea bind:value={newCommentText} placeholder="Write a comment..."></textarea>
        <button on:click={postComment}>Post</button>
      </div>
    {:else}
      <p class="login-prompt">Please <button on:click={handleLogin}>log in</button> to comment.</p>
    {/if}
  </aside>
{/if}

<style>
  :global(*) {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  :global(body) {
    font-family: 'Georgia', 'Times New Roman', serif;
    line-height: 1.6;
    color: #333;
    background-color: #fff;
  }

  .header {
    border-bottom: 1px solid #ddd;
    padding: 15px 0 10px 0;
    background-color: #fff;
    position: sticky;
    top: 0;
    z-index: 100;
  }

  .header-top {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: relative;
  }

  .date {
    font-size: 0.8em;
    color: #666;
  }

  .logo {
    font-size: 2.8em;
    font-weight: normal;
    color: #000;
    background: none;
    border: none;
    font-family: 'Old English Text MT', 'Times New Roman', serif;
    font-style: italic;
    cursor: pointer;
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
  }

  .user-info {
    font-size: 0.8em;
    color: #666;
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .login-btn {
    color: #326891;
    text-decoration: underline;
    background: none;
    border: none;
    cursor: pointer;
    font-family: inherit;
    font-size: inherit;
  }

  .publisher-badge {
    background: #326891;
    color: white;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 0.7em;
  }

  .hamburger {
    display: none;
    background: none;
    border: none;
    font-size: 1.5em;
    cursor: pointer;
  }

  .nav {
    background-color: #fff;
    border-bottom: 1px solid #ddd;
    padding: 10px 0;
  }

  .nav-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
    text-align: center;
  }

  .nav ul {
    list-style: none;
    display: inline-flex;
    gap: 20px;
    border: 1px solid #ddd;
    padding: 8px 15px;
    background-color: #f8f8f8;
  }

  .nav a {
    text-decoration: underline;
    color: #326891;
    font-size: 0.85em;
    font-weight: normal;
    transition: color 0.3s;
  }

  .nav a:hover,
  .nav a.active {
    color: #1a4d6b;
    font-weight: bold;
  }

  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 30px 20px;
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 40px;
    transition: filter 0.3s ease;
  }

  .container.blurred {
    filter: blur(3px);
  }

  .error-message,
  .loading {
    text-align: center;
    padding: 40px 20px;
    max-width: 1200px;
    margin: 0 auto;
  }

  .error-message button {
    margin-top: 10px;
    padding: 8px 16px;
    background: #326891;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

  .main-content {
    display: grid;
    gap: 30px;
  }

  .lead-story {
    border-bottom: 1px solid #ddd;
    padding-bottom: 30px;
  }

  .lead-image {
    width: 100%;
    max-height: 300px;
    object-fit: cover;
    margin-bottom: 15px;
  }

  .lead-story h1 {
    font-size: 2.2em;
    font-weight: bold;
    line-height: 1.2;
    margin-bottom: 15px;
    color: #000;
  }

  .lead-story h1 a {
    color: inherit;
    text-decoration: none;
  }

  .lead-story h1 a:hover {
    text-decoration: underline;
  }

  .lead-story .subtitle {
    font-size: 1.2em;
    color: #666;
    margin-bottom: 15px;
    font-weight: normal;
  }

  .lead-story .byline {
    font-size: 0.9em;
    color: #666;
    margin-bottom: 20px;
    font-style: italic;
  }

  .lead-story .excerpt {
    font-size: 1.1em;
    line-height: 1.7;
    color: #333;
    margin-bottom: 15px;
  }

  .secondary-stories {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 30px;
  }

  .story {
    border-bottom: 1px solid #eee;
    padding-bottom: 20px;
  }

  .story-image {
    width: 100%;
    max-height: 150px;
    object-fit: cover;
    margin-bottom: 10px;
  }

  .story h2 {
    font-size: 1.4em;
    font-weight: bold;
    line-height: 1.3;
    margin-bottom: 10px;
    color: #000;
  }

  .story h2 a {
    color: inherit;
    text-decoration: none;
  }

  .story h2 a:hover {
    text-decoration: underline;
  }

  .story .byline {
    font-size: 0.85em;
    color: #666;
    margin-bottom: 10px;
    font-style: italic;
  }

  .story .excerpt {
    font-size: 1em;
    line-height: 1.6;
    color: #333;
    margin-bottom: 10px;
  }

  .comment-button {
    background: #326891;
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.85em;
    transition: background-color 0.3s;
  }

  .comment-button:hover {
    background: #1a4d6b;
  }

  .comment-button.small {
    padding: 4px 8px;
    font-size: 0.75em;
  }

  .sidebar {
    border-left: 1px solid #ddd;
    padding-left: 30px;
  }

  .sidebar-section {
    margin-bottom: 40px;
  }

  .sidebar-section h3 {
    font-size: 1.3em;
    font-weight: bold;
    margin-bottom: 20px;
    color: #000;
    border-bottom: 2px solid #000;
    padding-bottom: 10px;
  }

  .sidebar-story {
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 1px solid #eee;
  }

  .sidebar-story:last-child {
    border-bottom: none;
  }

  .sidebar-story h4 {
    font-size: 1.1em;
    font-weight: bold;
    line-height: 1.3;
    margin-bottom: 8px;
    color: #000;
  }

  .sidebar-story h4 a {
    color: inherit;
    text-decoration: none;
  }

  .sidebar-story h4 a:hover {
    text-decoration: underline;
  }

  .sidebar-story .byline {
    font-size: 0.8em;
    color: #666;
    font-style: italic;
    margin-bottom: 5px;
  }

  .sidebar-story .excerpt {
    font-size: 0.9em;
    line-height: 1.5;
    color: #333;
    margin-bottom: 8px;
  }

  .opinion-section {
    background-color: #f9f9f9;
    padding: 30px;
    margin: 40px 0;
    border: 1px solid #ddd;
  }

  .opinion-section h3 {
    font-size: 1.5em;
    font-weight: bold;
    margin-bottom: 20px;
    color: #000;
  }

  .footer {
    background-color: #000;
    color: #fff;
    padding: 40px 0;
    margin-top: 50px;
  }

  .footer-content {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 30px;
  }

  .footer-section h4 {
    font-size: 1.1em;
    font-weight: bold;
    margin-bottom: 15px;
    color: #fff;
  }

  .footer-section ul {
    list-style: none;
  }

  .footer-section a {
    color: #ccc;
    text-decoration: none;
    font-size: 0.9em;
    line-height: 2;
    transition: color 0.3s;
  }

  .footer-section a:hover {
    color: #fff;
  }

  .comment-panel {
    position: fixed;
    top: 0;
    right: 0;
    width: 400px;
    height: 100vh;
    background: white;
    border-left: 1px solid #ddd;
    padding: 20px;
    overflow-y: auto;
    z-index: 1000;
    box-shadow: -2px 0 10px rgba(0,0,0,0.1);
  }

  .close-panel {
    position: absolute;
    top: 10px;
    right: 15px;
    background: none;
    border: none;
    font-size: 1.2em;
    cursor: pointer;
    color: #666;
  }

  .comment-list {
    margin: 20px 0;
    max-height: 60%;
    overflow-y: auto;
  }

  .comment-form {
    position: absolute;
    bottom: 20px;
    left: 20px;
    right: 20px;
  }

  .comment-form textarea {
    width: 100%;
    min-height: 80px;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-family: inherit;
    resize: vertical;
  }

  .comment-form button {
    margin-top: 10px;
    padding: 8px 16px;
    background: #326891;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

  .login-prompt {
    text-align: center;
    margin: 20px 0;
  }

  .login-prompt button {
    background: none;
    border: none;
    color: #326891;
    text-decoration: underline;
    cursor: pointer;
    font-family: inherit;
  }

  @media (max-width: 768px) {
    .hamburger {
      display: block;
    }

    .nav {
      display: none;
    }

    .nav.open {
      display: block;
      position: absolute;
      top: 100%;
      left: 0;
      right: 0;
      background: white;
      border-bottom: 1px solid #ddd;
      z-index: 99;
    }

    .nav.open ul {
      flex-direction: column;
      gap: 0;
      border: none;
      padding: 0;
      background: none;
    }

    .nav.open li {
      border-bottom: 1px solid #eee;
      padding: 10px 20px;
    }

    .logo {
      font-size: 2em;
      position: static;
      transform: none;
    }

    .header-top {
      flex-wrap: wrap;
      justify-content: center;
      gap: 10px;
    }

    .container {
      grid-template-columns: 1fr;
      gap: 30px;
    }

    .secondary-stories {
      grid-template-columns: 1fr;
    }

    .sidebar {
      border-left: none;
      border-top: 1px solid #ddd;
      padding-left: 0;
      padding-top: 30px;
    }

    .footer-content {
      grid-template-columns: 1fr 1fr;
    }

    .comment-panel {
      width: 100%;
      left: 0;
    }
  }

  @media (max-width: 480px) {
    .footer-content {
      grid-template-columns: 1fr;
    }

    .header-top {
      flex-direction: column;
      gap: 10px;
      text-align: center;
    }
  }
</style>