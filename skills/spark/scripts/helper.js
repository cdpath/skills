(function() {
  const ws = new WebSocket('ws://' + window.location.host);
  let buffer = [];
  ws.onopen = () => { buffer.forEach(m => ws.send(JSON.stringify(m))); buffer = []; };
  ws.onmessage = () => window.location.reload();

  function send(data) {
    const msg = { type: 'click', timestamp: Date.now(), ...data };
    if (ws.readyState === 1) ws.send(JSON.stringify(msg)); else buffer.push(msg);
  }

  document.body.addEventListener('click', (e) => {
    const choice = e.target.closest('[data-choice]');
    if (!choice) return;
    const siblings = choice.parentElement.querySelectorAll('[data-choice]');
    siblings.forEach(el => {
      if (!el.parentElement.classList.contains('options') || !el.parentElement.dataset.multiselect) {
        el.classList.remove('selected');
      }
    });
    choice.classList.toggle('selected');
    send({
      choice: choice.dataset.choice,
      label: choice.querySelector('h3')?.textContent || choice.dataset.choice,
      metadata: Object.fromEntries(Object.entries(choice.dataset).filter(([k]) => k !== 'choice'))
    });
    updateIndicator();
  });

  function updateIndicator() {
    const selected = document.querySelectorAll('.options [data-choice].selected, .cards [data-choice].selected');
    const text = document.getElementById('indicator-text');
    if (!text) return;
    const isMulti = document.querySelector('.options[data-multiselect], .cards[data-multiselect]');
    if (selected.length === 0) text.textContent = 'Click an option above, then return to the terminal';
    else if (selected.length === 1) text.textContent = 'Selected: ' + selected[0].dataset.choice;
    else text.textContent = 'Selected ' + selected.length + ' options';
  }

  window.toggleSelect = function(choiceId) {
    document.querySelectorAll('[data-choice]').forEach(el => {
      if (el.dataset.choice === choiceId) el.classList.toggle('selected');
    });
    updateIndicator();
  };

  window.brainstorm = {
    select: (choiceId) => { toggleSelect(choiceId); updateIndicator(); },
    deselect: (choiceId) => { document.querySelectorAll('[data-choice]').forEach(el => { if (el.dataset.choice === choiceId) el.classList.remove('selected'); }); updateIndicator(); },
    clear: () => { document.querySelectorAll('[data-choice]').forEach(el => el.classList.remove('selected')); updateIndicator(); },
    selected: () => Array.from(document.querySelectorAll('[data-choice].selected')).map(el => el.dataset.choice)
  };
})();
