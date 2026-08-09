document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('predict-age-form');
  const resultBox = document.getElementById('predict-result');
  if (!form || !resultBox) return;

  form.addEventListener('submit', async function (ev) {
    ev.preventDefault();
    resultBox.textContent = 'Predicting...';
    resultBox.classList.remove('error');
    const url = form.action;
    try {
      const resp = await fetch(url, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
      });
      const data = await resp.json();
      if (data.status === 'ok') {
        resultBox.textContent = 'Predicted age: ' + data.predicted_age;
        // show top matches
        if (data.top && data.top.length) {
          const list = document.createElement('ul');
          list.className = 'predict-top-list';
          data.top.slice(0,5).forEach(t => {
            const li = document.createElement('li');
            li.textContent = `${t.filename} — age:${t.age} (dist:${t.distance})`;
            list.appendChild(li);
          });
          // replace any existing list
          const existing = resultBox.querySelector('ul');
          if (existing) existing.remove();
          resultBox.appendChild(list);
        }
      } else {
        resultBox.textContent = data.message || 'Prediction failed';
        resultBox.classList.add('error');
      }
    } catch (err) {
      resultBox.textContent = 'Prediction request failed';
      resultBox.classList.add('error');
    }
  });
});
