async function submitRating(itemId) {
  const select = document.getElementById('rating-select');
  const commentEl = document.getElementById('rating-comment');
  const resultEl = document.getElementById('rating-result');
  if (!select || !resultEl) return;

  if (!window.LOGGED_IN) {
    window.location.href = window.LOGIN_URL || '/auth';
    return;
  }

  const rating = select.value;
  const comment = commentEl ? commentEl.value : '';
  resultEl.textContent = 'Sending...';

  try {
    const formData = new FormData();
    formData.append('rating', rating);
    formData.append('comment', comment);

    const resp = await fetch(`/items/${itemId}/review`, {
      method: 'POST',
      body: formData,
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      },
      credentials: 'same-origin'
    });

    const data = await resp.json();
    if (data.status === 'ok') {
      // update window.ITEMS and UI
      const item = window.ITEMS.find(i => i.id === itemId);
      if (item) {
        item.rating = data.rating;
        item.reviews = data.reviews;
      }
      const ratingSpan = document.querySelector('.item-rating');
      if (ratingSpan) ratingSpan.textContent = `⭐ ${data.rating} (${data.reviews} reviews)`;
      resultEl.textContent = 'Thanks!';
      resultEl.classList.remove('error');
    } else {
      resultEl.textContent = data.message || 'Failed';
      resultEl.classList.add('error');
    }
  } catch (err) {
    resultEl.textContent = 'Request failed';
    resultEl.classList.add('error');
  }
}
