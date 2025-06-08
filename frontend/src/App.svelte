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
  let articlePanelOpen = false;
  let selectedFullArticle = null;
  let imageInput;

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

  async function openArticlePanel(article) {
    selectedFullArticle = article;
    articlePanelOpen = true;
  }

  function closeArticlePanel() {
    articlePanelOpen = false;
    selectedFullArticle = null;
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
      if (user?.name === 'moderator' || user?.name === 'publisher') {
        articles = result.articles;
      } else {
        articles = result.articles.filter(a => a.approved === true);
      }
      fetchError = result.fetchError;
    } catch (e) {
      console.error('Failed to load section:', e);
      fetchError = true;
    }
  }

  $: leadStory = articles.length > 0 ? articles[0] : fallbackData.leadStory;
  
  $: secondaryStories = articles.length > 1 ? articles.slice(1, 5) : fallbackData.secondaryStories;
  
  $: sidebarStories = articles.length > 5 ? articles.slice(5, 8) : [];

  export let popUpOpen = false;

  let headline = '';
  let abstract = '';
  let section_name = '';
  let body = '';
  let errorMsg = '';
  let successMsg = '';

  function openPopUp() {
    popUpOpen = true;
  }

  function closePopUp() {
    popUpOpen = false; 
  }

  function toggleDarkMode() {
    document.body.classList.toggle('dark');
    const isDark = document.body.classList.contains('dark');
    localStorage.setItem('darkMode', isDark ? 'true' : 'false');
  }

  // change file format to binary
  function fileToBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result);
      reader.onerror = error => reject(error);
    });
  }

  async function submitArticle() {
    errorMsg = '';
    successMsg = '';

    let multimediaData = null;
    if (imageInput.files.length > 0) {
      multimediaData = await fileToBase64(imageInput.files[0]);
    }

    try {
      const response = await fetch('/api/articles', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          headline,
          abstract,
          section_name,
          body,
          multimedia: multimediaData
        })
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Failed to submit article');
      }

      successMsg = 'Article successfully submitted!';
      headline = abstract = section_name = body = '';
      if (imageInput) imageInput.value = '';
    } catch (err) {
      errorMsg = err.message;
    }
  }

  let unapprovedArticles = [];
  async function fetchUnapprovedArticles() {
    try {
      const res = await fetch('/api/articles/pending');
      if (res.ok) {
        const data = await res.json();
        unapprovedArticles = data.articles;
      }
    } catch (e) {
      console.error('Failed to fetch unapproved articles:', e);
    }
  }

  async function deleteArticle(articleId) {
    if (!confirm("Are you sure you want to delete this article?")) return;
    try {
      const res = await fetch(`/api/article?article_id=${articleId}`, {
        method: 'DELETE'
      });
      if (res.ok) {
      await loadSection(currentSection);
    } else {
      const err = await res.json();
      alert(`Failed to delete article: ${err.error}`);
    }
    } catch (e) {
      console.error('Error deleting article:', e);
    }
  }

  async function approveArticle(articleId) {
    try {
      const res = await fetch(`/api/article/approve`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ article_id: articleId }),
      });
      if (res.ok) {
        await fetchUnapprovedArticles();
        await loadSection(currentSection);
      } else {
        console.error('Failed to approve article');
      }
    } catch (e) {
      console.error('Error approving article:', e);
    }
  }


  onMount(async () => {
    today = new Date().toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });

    const savedMode = localStorage.getItem('darkMode');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (savedMode === 'true' || (savedMode === null && prefersDark)) {
      document.body.classList.add('dark');
    }

    try {
      const res = await fetch('/api/user', { credentials: 'include' });
      user = await res.json();
    } catch (e) {
      user = null;
    }

    if (user?.name === 'moderator') {
      await fetchUnapprovedArticles();
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
          <span class="publisher-badge" on:click={openPopUp}>Publish Article</span>
        {/if}
      {:else}
        <button class="login-btn" on:click={handleLogin}>Login</button>
      {/if}
      <button class="dark-toggle" on:click={toggleDarkMode}>
        🌓
      </button>
    </div>
    
    <button class="hamburger {menuOpen ? 'open' : ''}" on:click={toggleMenu}>☰</button>
  </div>
  
</header>

{#if popUpOpen}
  <div class="PopUp" id="PopUp">
    <div class="PopUpHeader">
      <h1 class="ASP">Article Submission Process</h1>
      <button class="close-popup" on:click={closePopUp}>✖</button>
    </div>

    <form on:submit|preventDefault={submitArticle}>
      <div class="hlineForm">
        <label for="headline">Headline</label>
      </div>
      <div class="hlineInput">
        <input type="text" id="headline" bind:value={headline} placeholder="Your Headline Here..." required />
      </div>

      <div class="hlineForm">
        <label for="abstract">Abstract</label>
      </div>
      <div class="hlineInput">
        <input type="text" id="abstract" bind:value={abstract} placeholder="Short abstract..." required />
      </div>

      <div class="hlineForm">
        <label for="section">Section</label>
      </div>
      <div class="hlineInput">
        <select id="section" bind:value={section_name} required>
          <option value="" disabled selected>Select a section...</option>
          <option value="local">Local</option>
          <option value="us">U.S.</option>
          <option value="world">World</option>
          <option value="climate">Climate</option>
          <option value="arts">Arts</option>
          <option value="opinion">Opinion</option>
        </select>
      </div>

      <div class="artcontentForm">
        <label for="body">Article Content</label>
      </div>
      <div class="bodyInput">
        <textarea id="body" bind:value={body} placeholder="Your Article Here..." required></textarea>
      </div>

      <div class="imageInput">
        <input type="file" id="image" bind:this={imageInput} />
      </div>

      <div class="submitArticle">
        <button type="submit">Submit Article</button>
      </div>
    </form>

    {#if errorMsg}
      <p class="error-msg">{errorMsg}</p>
    {/if}
    {#if successMsg}
      <p class="success-msg">{successMsg}</p>
    {/if}
  </div>
{/if}

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
  <div class="container {commentPanelOpen || articlePanelOpen ? 'blurred' : ''}">
    <main class="main-content">
      <article class="lead-story">
        {#if leadStory.multimedia}
          {#if typeof leadStory.multimedia === 'string'}
            <img src={leadStory.multimedia} alt="Article image" class="story-image"/>
          {:else}
            <img src={leadStory.multimedia.url || leadStory.multimedia.default?.url} alt="Lead story image" class="lead-image" />
          {/if}
        {/if}
        <h1>
          <!-- Updated: Made headline clickable to open article panel -->
          <button class="article-link" on:click={() => openArticlePanel(leadStory)}>
            {leadStory.headline?.main || leadStory.title}
          </button>
        </h1>
        {#if leadStory.subtitle}
          <p class="subtitle">{leadStory.subtitle}</p>
        {/if}
        <p class="byline">
          {#if typeof leadStory.byline === 'string'}
            {leadStory.byline}
          {:else if leadStory.byline?.original}
            {leadStory.byline.original}
          {:else}
            Anonymous        
          {/if}
        </p>
        <p class="excerpt">{leadStory.abstract || leadStory.excerpt}</p>
        {#if leadStory._id}
          <button class="comment-button" on:click={() => openComments(leadStory)}>💬 Comment</button>
        {/if}
        {#if user?.name === 'moderator'}
          <button class="comment-button" on:click={() => deleteArticle(leadStory._id)}>🗑 Delete Article</button>
        {/if}
      </article>

      <section class="secondary-stories">
        {#each secondaryStories as story}
          <article class="story">
            {#if story.multimedia}
              {#if typeof story.multimedia === 'string'}
                <img src={story.multimedia} alt="Article image" class="story-image"/>
              {:else}
                <img src={story.multimedia.url || story.multimedia.default?.url} alt="Article image" class="story-image" />
              {/if}
            {/if}
            <h2>
              <!-- Updated: Made headline clickable to open article panel -->
              <button class="article-link" on:click={() => openArticlePanel(story)}>
                {story.headline?.main || story.title}
              </button>
            </h2>
            <p class="byline">
              {#if typeof story.byline === 'string'}
                {story.byline}
              {:else if story.byline?.original}
                {story.byline.original}
              {:else}
                Anonymous      
              {/if}      
            </p>
            <p class="excerpt">{story.abstract || story.excerpt}</p>
            {#if story._id}
              <button class="comment-button" on:click={() => openComments(story)}>💬 Comment</button>
            {/if}
            {#if user?.name === 'moderator'}
              <button class="comment-button" on:click={() => deleteArticle(story._id)}>🗑 Delete</button>
            {/if}
          </article>
        {/each}
      </section>

      {#if currentSection === 'Opinion' && articles.length > 0}
        <section class="opinion-section">
          <h3>Opinion</h3>
          <article class="story">
            <h2>
              <!-- Updated: Made headline clickable to open article panel -->
              <button class="article-link" on:click={() => openArticlePanel(articles[0])}>
                {articles[0].headline?.main || articles[0].title}
              </button>
            </h2>
            <p class="byline">
              {#if typeof articles[0].byline === 'string'}
                {articles[0].byline}
              {:else if articles[0].byline?.original}
                {articles[0].byline.original}
              {:else}
                Anonymous
              {/if}            
            </p>
            <p class="excerpt">{articles[0].abstract || articles[0].excerpt}</p>
            {#if articles[0]._id}
              <button class="comment-button" on:click={() => openComments(articles[0])}>💬 Comment</button>
            {/if}
            {#if user?.name === 'moderator'}
              <button class="comment-button" on:click={() => deleteArticle(articles[0]._id)}>🗑 Delete</button>
            {/if}
          </article>
        </section>
      {/if}
    </main>

    {#if user?.name === 'moderator'}
      <section class="opinion-section">
        <h3>Pending Approval</h3>
        {#each unapprovedArticles as pending}
          <article class="story">
            <h2>{pending.headline?.main || pending.title}</h2>
            <p class="byline">{pending.byline?.original || pending.byline}</p>
            <p class="excerpt">{pending.abstract?.text || pending.abstract}</p>
            <button class="comment-button" on:click={() => approveArticle(pending._id)}>✅ Approve</button>
            <button class="comment-button" on:click={() => deleteArticle(pending._id)}>🗑 Delete</button>
          </article>
        {/each}
      </section>
    {/if}


    <aside class="sidebar">
      <section class="sidebar-section">
        <h3>Most Popular</h3>
        {#each sidebarStories as story}
          <article class="sidebar-story">
            <h4>
              <!-- Updated: Made headline clickable to open article panel -->
              <button class="article-link small" on:click={() => openArticlePanel(story)}>
                {story.headline?.main || story.title}
              </button>
            </h4>
            <p class="byline">
              {#if typeof story.byline === 'string'}
                {story.byline}
              {:else if story.byline?.original}
                {story.byline.original}
              {:else}
                Anonymous
              {/if}
            </p>
            <p class="excerpt">{(story.abstract || story.excerpt || '').substring(0, 100)}...</p>
            {#if story._id}
              <button class="comment-button small" on:click={() => openComments(story)}>💬</button>
            {/if}
            {#if user?.name === 'moderator'}
              <button class="comment-button" on:click={() => deleteArticle(story._id)}>🗑</button>
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

{#if articlePanelOpen && selectedFullArticle}
  <div class="article-panel">
    <div class="article-panel-header">
      <button class="close-panel" on:click={closeArticlePanel}>✖</button>
      <div class="article-actions">
        {#if selectedFullArticle._id}
          <button class="comment-button" on:click={() => openComments(selectedFullArticle)}>💬 Comment</button>
        {/if}
        {#if user?.name === 'moderator'}
          <button class="comment-button" on:click={() => deleteArticle(selectedFullArticle._id)}>🗑 Delete</button>
        {/if}
      </div>
    </div>
    
    <div class="article-panel-content">
      <div class="article-meta">
        <span class="article-section">{currentSection}</span>
        <span class="article-date">{today}</span>
      </div>
      
      <h1 class="article-title">{selectedFullArticle.headline?.main || selectedFullArticle.title}</h1>
      
      {#if selectedFullArticle.subtitle}
        <p class="article-subtitle">{selectedFullArticle.subtitle}</p>
      {/if}
      
      <p class="article-byline">{selectedFullArticle.byline?.original || selectedFullArticle.byline}</p>
      
      {#if selectedFullArticle.multimedia}
        <div class="article-image-container">
          {#if typeof selectedFullArticle.multimedia === 'string'}
            <img src={selectedFullArticle.multimedia} alt="Article image" class="article-full-image" />
          {:else}
            <img 
              src={selectedFullArticle.multimedia.url || selectedFullArticle.multimedia.default?.url} 
              alt="Article image" 
              class="article-full-image" 
            />
          {/if}
          {#if selectedFullArticle.multimedia.caption}
            <p class="image-caption">{selectedFullArticle.multimedia.caption}</p>
          {/if}
        </div>
      {/if}
      
      <div class="article-body">
        {#if selectedFullArticle.body}
          <!-- If you have full body content from your API -->
          {@html selectedFullArticle.body.replace(/\n/g, '<br><br>')}
        {:else}
          <!-- Fallback to abstract/excerpt -->
          <p>{selectedFullArticle.abstract || selectedFullArticle.excerpt}</p>
          {#if selectedFullArticle.web_url && selectedFullArticle.web_url !== '#'}
            <p><a href={selectedFullArticle.web_url} target="_blank" rel="noopener noreferrer">Read full article on original source →</a></p>
          {/if}
        {/if}
      </div>
    </div>
  </div>
{/if}

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
  @import 'app.css';
</style>
