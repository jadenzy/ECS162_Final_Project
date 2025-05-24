export async function fetchArticles(section = '') {
    let fetchError = false;
    let articles = [];
    try {
        const url = section ? `/api/articles?section=${encodeURIComponent(section)}` : '/api/articles';
        const response = await fetch(url); 
        const data = await response.json();

        if (data.error) throw new Error(data.error);
        articles = data.articles;

    } catch (error) {
        fetchError = true;
        console.error('Failed to fetch articles:', error);
    }

    return { articles, fetchError };
}
