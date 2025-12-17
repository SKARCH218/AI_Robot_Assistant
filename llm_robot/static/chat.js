// (구) 위임 클릭 핸들러 제거: 아래 개별 버튼 핸들러만 사용
// 버튼 DOM 존재 여부 확인
console.log('home-btn:', !!document.getElementById('home-btn'));
console.log('replay-btn:', !!document.getElementById('replay-btn'));
console.log('emergency-btn:', !!document.getElementById('emergency-btn'));
console.log('clear-btn:', !!document.getElementById('clear-btn'));
console.log("chat.js loaded");
// 간단 토스트 유틸
function showToast(msg, ms = 1800) {
    const el = document.getElementById('toast');
    if (!el) { console.log('[TOAST]', msg); return; }
    el.textContent = msg;
    el.style.display = 'block';
    el.style.opacity = '1';
    el.style.transition = '';
    setTimeout(() => {
        el.style.transition = 'opacity 280ms';
        el.style.opacity = '0';
        setTimeout(() => { el.style.display = 'none'; el.style.transition = ''; }, 320);
    }, ms);
}
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatBox = document.getElementById('chat-box');
    const imageInput = document.getElementById('image-input');
    const imagePreview = document.getElementById('image-preview');
    const previewImage = document.getElementById('preview-image');
    const removeImageBtn = document.getElementById('remove-image');

    // 이미지 업로드 관련 이벤트 (vision이 활성화된 경우에만)
    if (imageInput) {
        imageInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file && file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewImage.src = e.target.result;
                    imagePreview.style.display = 'block';
                };
                reader.readAsDataURL(file);
            }
        });
    }

    if (removeImageBtn) {
        removeImageBtn.addEventListener('click', function() {
            imageInput.value = '';
            imagePreview.style.display = 'none';
            previewImage.src = '';
        });
    }

    chatInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            chatForm.requestSubmit();
        }
    });

    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const value = chatInput.value.trim();
        if (!value) return;
        chatInput.value = '';
        
        // 이미지가 있는지 확인 (vision이 활성화된 경우에만)
        const hasImage = imageInput && imageInput.files.length > 0;
        let userMessage = value;
        if (hasImage) {
            userMessage += ' 📸';
        }
        
        // 사용자 말풍선 추가
        const userDiv = document.createElement('div');
        userDiv.className = 'user';
        userDiv.innerHTML = '<div style="font-size:0.95em; color:#555; font-weight:bold; margin-bottom:2px; text-align:right;">나</div>' +
            '<span class="bubble">' + userMessage + '</span>';
        chatBox.appendChild(userDiv);
        
        // AI 응답 대기 말풍선(생각중) 추가
        const botDiv = document.createElement('div');
        botDiv.className = 'bot';
        const thinkingMessage = hasImage ? 'DOFBOT이 이미지를 분석중이에요! 🔍...' : 'DOFBOT이 생각중이에요! ...';
        botDiv.innerHTML = '<div style="font-size:0.95em; color:#007bff; font-weight:bold; margin-bottom:2px;">DOFBOT</div>' +
            '<span class="bubble pending">' + thinkingMessage + '</span>';
        chatBox.appendChild(botDiv);
        chatBox.scrollTop = chatBox.scrollHeight;

        // FormData로 이미지와 텍스트 모두 전송
        const formData = new FormData();
        formData.append('prompt', value);
        if (hasImage) {
            formData.append('image', imageInput.files[0]);
        }

        // 서버에 AJAX로 POST 요청
        fetch('/', {
            method: 'POST',
            body: formData
        })
        .then(response => response.text())
        .then(html => {
            try {
                // 이미지 미리보기 정리 (vision이 활성화된 경우에만)
                if (imageInput) {
                    imageInput.value = '';
                }
                if (imagePreview) {
                    imagePreview.style.display = 'none';
                }
                if (previewImage) {
                    previewImage.src = '';
                }
                
                // 전체 채팅 박스만 갱신
                const temp = document.createElement('div');
                temp.innerHTML = html;
                const newChatBox = temp.querySelector('#chat-box');
                if (newChatBox && newChatBox.innerHTML.trim()) {
                    chatBox.innerHTML = newChatBox.innerHTML;
                    setTimeout(function() {
                        chatBox.scrollTop = chatBox.scrollHeight;
                    }, 30);
                } else {
                    // 빈 응답이나 예상치 못한 응답 처리
                    const pendingBubble = chatBox.querySelector('.bubble.pending');
                    if (pendingBubble) {
                        pendingBubble.textContent = '응답을 처리하는 중에 문제가 발생했어요. 다시 시도해주세요! 🤔';
                        pendingBubble.className = 'bubble error';
                        pendingBubble.style.backgroundColor = '#ffe6e6';
                        pendingBubble.style.color = '#d32f2f';
                    }
                }
            } catch (e) {
                console.error('chat update error', e);
                location.reload();
            }
        })
        .catch(err => {
            console.error('chat submit error', err);
            // 오류 발생 시 "생각중" 메시지를 오류 메시지로 교체
            const pendingBubble = chatBox.querySelector('.bubble.pending');
            if (pendingBubble) {
                pendingBubble.textContent = '죄송해요, 응답에 문제가 있었어요. 다시 말씀해주세요! 😅';
                pendingBubble.className = 'bubble error';
                pendingBubble.style.backgroundColor = '#ffe6e6';
                pendingBubble.style.color = '#d32f2f';
            }
        });
    });

    // 각도 수정 버튼 클릭 시 입력창 표시 및 처리
    document.querySelectorAll('.edit-angle-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            var motor = btn.getAttribute('data-motor');
            var angleSpan = document.getElementById('angle-' + motor);
            var current = angleSpan.textContent.trim();
            var input = document.createElement('input');
            input.type = 'number';
            input.min = 0;
            input.max = 180;
            input.value = current;
            input.style.width = '60px';
            input.style.fontSize = '1em';
            input.style.marginLeft = '8px';
            input.style.borderRadius = '6px';
            input.style.border = '1px solid #007bff';
            input.style.padding = '2px 6px';
            input.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') {
                    var val = parseInt(input.value);
                    if (!isNaN(val) && val >= 0 && val <= 180) {
                        // PATCH /angles API로 변경 요청
                        fetch('/angles', {
                            method: 'PATCH',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ motor: motor, angle: val })
                        }).then(res => res.json()).then(data => {
                            if (data.success) {
                                angleSpan.textContent = val;
                                input.remove();
                            } else {
                                input.style.border = '1.5px solid #ff3333';
                            }
                        }).catch(() => {
                            input.style.border = '1.5px solid #ff3333';
                        });
                    } else {
                        input.style.border = '1.5px solid #ff3333';
                    }
                }
                if (e.key === 'Escape') {
                    input.remove();
                }
            });
            angleSpan.parentNode.appendChild(input);
            input.focus();
        });
    });
    // 홈 자세 복귀 버튼 클릭 시 /home API 호출
    const homeBtn = document.getElementById('home-btn');
    if (homeBtn) {
        homeBtn.addEventListener('click', function() {
            console.log('홈자세 버튼 클릭');
            fetch('/home', { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    if (data.success && data.angles) {
                        Object.entries(data.angles).forEach(([motor, val]) => {
                            var span = document.getElementById('angle-' + motor);
                            if (span) span.textContent = val;
                        });
                    }
                });
        });
    }

    // 동작 재실행 버튼
    const replayBtn = document.getElementById('replay-btn');
    if (replayBtn) {
    replayBtn.addEventListener('click', function() {
            console.log('동작재실행 버튼 클릭');
        fetch('/replay', { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
            showToast('최근 동작 명령이 재실행되었습니다.');
                    } else {
            showToast('재실행 실패: ' + (data.error || '오류'));
                    }
        })
        .catch(err => showToast('재실행 오류: ' + err));
        });
    }

    // 긴급정지 버튼
    const emergencyBtn = document.getElementById('emergency-btn');
    if (emergencyBtn) {
    emergencyBtn.addEventListener('click', function() {
            console.log('긴급정지 버튼 클릭');
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 3000);
        fetch('/emergency_stop', { method: 'POST', signal: controller.signal })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
            showToast('로봇이 즉시 정지되었습니다.');
                    } else {
            showToast('정지 실패: ' + (data.error || '오류'));
                    }
        })
        .catch(err => showToast('정지 호출 오류: ' + (err?.name === 'AbortError' ? '타임아웃' : err)))
        .finally(() => clearTimeout(timer));
        });
    }

    // IIFE closing removed to fix syntax error
    const clearBtn = document.getElementById('clear-btn');
    if (clearBtn) {
    clearBtn.addEventListener('click', function() {
            console.log('채팅내역지우기 버튼 클릭');
            fetch('/clear_log', { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
            showToast('대화내역이 모두 삭제되었습니다.');
            setTimeout(() => location.reload(), 400);
                    } else {
            showToast('삭제 실패: ' + (data.error || '오류'));
                    }
        })
        .catch(err => showToast('삭제 호출 오류: ' + err));
        });
    }

    // 학습 상태 보기 버튼
    const memoryBtn = document.getElementById('memory-btn');
    if (memoryBtn) {
        memoryBtn.addEventListener('click', function() {
            console.log('학습상태 버튼 클릭');
            fetch('/memory_status', { method: 'GET' })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        const personality = data.personality_traits;
                        const analysis = data.conversation_analysis;
                        const totalConversations = data.total_conversations;
                        
                        const memoryInfo = `
🤖 DOFBOT 학습 상태:

📊 성격 특성:
• 친근함: ${personality.friendliness_level}/10
• 도움정도: ${personality.helpfulness_level}/10  
• 장난기: ${personality.playfulness_level}/10

📈 대화 분석:
${analysis}

💬 총 대화 수: ${totalConversations}개

🧠 최근 학습 맥락:
${data.recent_context}
                        `;
                        
                        // 모달 창으로 정보 표시
                        if (confirm(memoryInfo + '\n\n메모리를 초기화하시겠습니까?')) {
                            fetch('/reset_memory', { method: 'POST' })
                                .then(res => res.json())
                                .then(resetData => {
                                    if (resetData.success) {
                                        showToast('학습 메모리가 초기화되었습니다.');
                                    } else {
                                        showToast('메모리 초기화 실패: ' + resetData.error);
                                    }
                                });
                        }
                    } else {
                        showToast('학습 상태를 불러올 수 없습니다: ' + data.error);
                    }
                })
                .catch(err => showToast('학습 상태 조회 오류: ' + err));
        });
    }
// ...기존 코드...