<script>
    import CommentItem from './CommentItem.svelte';
    export let comment;
    export let replies = [];
    export let user;
    export let onReply;
    export let onDelete;
    export let onRedact;
    export let getReplies; 
  </script>

  <div class="comment {comment.parent_id ? 'reply-comment' : 'main-comment'}">
    <strong>{comment.user}</strong>:
    <div class="comment-text">
      {comment.redacted_text ? comment.redacted_text : comment.text}
    </div>

    <div class="mod-tools">
      <div class="left-buttons">
        {#if user && !user.error}
          <button class="reply-btn" on:click={() => onReply(comment._id)}>Reply</button>
        {:else}
          <button class="reply-btn" on:click={() => window.location.href = '/login'}>Log in to Reply</button>
        {/if}

        {#if user?.name === 'moderator' || comment.user === user?.name}
            {#if user?.name === 'moderator'}
              <button class="redact-btn" on:click={() => onRedact(comment._id, comment.text)}>Redact</button>
            {/if}
            <button class="delete-btn" on:click={() => onDelete(comment._id)}>Delete</button>
        {/if}
      </div>
    </div>
  
    <div class="replies">
      {#each getReplies(comment._id) as reply}
        <CommentItem
          {reply}
          comment={reply}
          replies={getReplies(reply._id)}
          {user}
          {onReply}
          {onDelete}
          {onRedact}
          {getReplies}
        />
      {/each}
    </div>
  </div>
  
  <style>
    .comment {
      margin-bottom: 1rem;
      padding: 0.75rem;
    }

    .main-comment {
      border-bottom: 1px solid #ccc;
    }

    .reply-comment {
      background: none;
      padding: 0.5rem 0;
      border-bottom: none;
    }

    .comment-text {
      margin-top: 0.25rem;
      margin-bottom: 0.5rem;
      line-height: 1.5;
    }

    .mod-tools {
      margin-top: 1.2rem;
      margin-bottom: 0.5rem;
    }

    .left-buttons {
      display: flex;
      gap: 0.5rem;
    }

    .reply-btn {
      color: #326891;
    }

    .redact-btn {
      color: #666666;
    }

    .delete-btn {
      color: #666666;
      margin-left: auto;
    }

    button {
      all: unset;
      cursor: pointer;
      font-size: 0.9rem;
      font-weight: bolder;   
      padding-top: 0.2rem;    
      padding-bottom: 0.2rem;    
      border-radius: 0.5rem; 
    }

    button:hover {
      background-color: rgba(74, 109, 140, 0.1);
    }

    .replies {
      margin-left: 1.5rem;
      border-left: 1px solid #ccc;
      padding-left: 1rem;
    }
  </style>
  