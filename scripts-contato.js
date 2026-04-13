// scripts-contato.js
// Funções JS migradas do inline de contato.html

// MENU MOBILE
function toggleMenu() {
  const navLinks = document.getElementById('navLinks');
  navLinks.classList.toggle('mobile-open');
}

// WHATSAPP TOGGLE
function toggleWA() {
  const popup = document.getElementById('wpPopup');
  popup.classList.toggle('open');
}

// FECHAR EXIT POPUP
function closeExit() {
  document.getElementById('exitPopup').classList.remove('show');
}

// EXIT INTENT
let exitShown = false;
function maybeShowExit() {
  if (exitShown) return;
  let count = parseInt(sessionStorage.getItem('tabSwitchCount') || '0') + 1;
  sessionStorage.setItem('tabSwitchCount', count);
  if (count % 3 === 0) {
    exitShown = true;
    document.getElementById('exitPopup').classList.add('show');
  }
}
document.addEventListener('visibilitychange', function() {
  if (document.visibilityState === 'hidden') {
    maybeShowExit();
  }
});

// NAVBAR SCROLL
window.addEventListener('scroll', function() {
  const nav = document.getElementById('navbar');
  if (window.scrollY > 50) {
    nav.style.background = 'rgba(255,255,255,0.98)';
    nav.style.boxShadow = '0 2px 20px rgba(0,0,0,0.06)';
  } else {
    nav.style.background = 'rgba(255,255,255,0.85)';
    nav.style.boxShadow = 'none';
  }
});

// FECHAR MENU AO CLICAR EM LINK
window.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.nav-links a').forEach(link => {
    link.addEventListener('click', () => {
      document.getElementById('navLinks').classList.remove('mobile-open');
    });
  });

  // FORMULÁRIO COM EMAILJS
  if (typeof emailjs !== 'undefined') {
    emailjs.init('BDUWYY3eicXTr361g');
  }
  const form = document.getElementById('contactForm');
  if (form) {
    const enviarBtn = document.getElementById('enviarBtn');
    const recaptchaContainer = document.getElementById('recaptcha-container');
    let captchaShown = false;
    enviarBtn.addEventListener('click', function() {
      if (!captchaShown) {
        recaptchaContainer.style.display = 'block';
        captchaShown = true;
        return;
      }
      // Verifica se o captcha foi resolvido
      const recaptchaResponse = grecaptcha.getResponse();
      if (!recaptchaResponse) {
        alert('Por favor, resolva o captcha para enviar.');
        return;
      }
      // Validação de conteúdo suspeito (links, URLs, HTML, etc)
      const nome = form.querySelector('input[name="nome"]').value;
      const email = form.querySelector('input[name="email"]').value;
      const assunto = form.querySelector('select[name="assunto"]').value;
      const mensagem = form.querySelector('textarea[name="mensagem"]').value;
      // Regex para bloquear links, URLs, HTML tags e palavras suspeitas
      const forbiddenPattern = /(https?:\/\/|www\.|<[^>]+>|href=|src=|@|\.com|\.net|\.org|\.br|\[url|\[link|\[href|\[src|<script|<iframe|<img|<a |<form|<input|<button|<object|<embed|<svg|<base|<meta|<style|<link|<body|<head|<html|<title|<div|<span|<table|<tr|<td|<th|<ul|<li|<ol|<dl|<dt|<dd|<fieldset|<legend|<textarea|<select|<option|<iframe|<frame|<frameset|<applet|<bgsound|<layer|<ilayer|<xml|<xss|<script|onload|onerror|svg|math|base|object|embed|form|input|button|textarea|select|option|iframe|frame|frameset|applet|bgsound|layer|ilayer|xml|xss|ftp:\/\/|mailto:|javascript:|data:|base64,|%3C|%3E|"|'|{|}|\[|\]|\^|\*|\$|\(|\)|=|\+|~|`|\|)/i;
      if (forbiddenPattern.test(mensagem) || forbiddenPattern.test(nome) || forbiddenPattern.test(email) || forbiddenPattern.test(assunto)) {
        alert('Por favor, preencha o formulário apenas com texto válido. Não são permitidos links, URLs ou conteúdo suspeito.');
        return;
      }
      if (typeof emailjs !== 'undefined' && emailjs.send) {
        emailjs.send("service_w9kqeif", "template_cl4knzx", {
          nome, email, assunto, mensagem
        })
        .then(function() {
          alert('Mensagem enviada com sucesso!');
          form.reset();
          grecaptcha.reset();
          recaptchaContainer.style.display = 'none';
          captchaShown = false;
        }, function(error) {
          alert('Erro ao enviar mensagem. Tente novamente.');
          console.log('Erro:', error);
        });
      } else {
        alert('Formulário enviado com sucesso! Entraremos em contato.');
        form.reset();
        grecaptcha.reset();
        recaptchaContainer.style.display = 'none';
        captchaShown = false;
      }
    });
  }
});
