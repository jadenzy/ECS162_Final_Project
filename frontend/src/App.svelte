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
  @import './app.css';
</style>