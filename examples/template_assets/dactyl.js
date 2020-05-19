// Events ----------------------------------------------------------------------
$(document).ready(() => {
  // // Mobile menu.
  // $('[data-toggle="slide-collapse"]').on('click', () => {
  //   $navMenuCont = $($(this).data('target'))
  //   $navMenuCont.toggleClass('show')
  //   $(".menu-overlay").toggleClass('active')
  // })
  // $(".menu-overlay").click(function(event) {
  //   $(".navbar-toggler").trigger("click")
  // })

  // Jump to Top Button
  var TO_TOP_MIN = 50
  var TO_TOP_SPEED = 500
  var TO_TOP_POS = 0
  $(window).scroll(function () {
    if ($(this).scrollTop() > TO_TOP_MIN) {
       $('.jump-to-top').fadeIn()
    } else {
       $('.jump-to-top').fadeOut()
    }
  })
  $(".jump-to-top").click(() => {
    $("body").animate({scrollTop: TO_TOP_POS}, TO_TOP_SPEED)
  })
})

// Helper functions for interactive tutorials ----------------------------------

function slugify(s) {
  const unacceptable_chars = /[^A-Za-z0-9._ ]+/
  const whitespace_regex = /\s+/
  s = s.replace(unacceptable_chars, "")
  s = s.replace(whitespace_regex, "_")
  s = s.toLowerCase()
  if (!s) {
    s = "_"
  }
  return s
}

function complete_step(step_name) {
  const step_id = slugify(step_name)
  $(".bc-"+step_id).removeClass("active").addClass("done")
  $(".bc-"+step_id).next().removeClass("disabled").addClass("active")
}

// Expandable // Collapsible Code Tabs -----------------------------------------
function make_code_expandable() {
  function has_scrollbars(e) {
    if ($(e).parents(".multicode").length > 0) {
      //TODO: figure out if we can detect scrollbars on non-default tabs of
      // multicode samples. For now, always consider multi-code sections to
      // need scrollbars.
      return true;
    }
    return (e.scrollHeight > e.clientHeight) || (e.scrollWidth > e.clientWidth);
  }

  var toggle_cs = function(eo) {
      //eo = $("#"+id);
      var wrapper = $(eo.target).parent();
      var code_el = wrapper.find("code");
      code_el.toggleClass('expanded');
      var placeholders = wrapper.find(".code-placeholder");
      if (placeholders.length) {
          placeholders.remove();
      } else {
          code_el.after("<div class='code-placeholder' style='width:"
                              + code_el.width()
                              + "px; height:"
                              + code_el.height()
                              + "px;'>&nbsp;</div>");
      }
      current_button_text = wrapper.find(".code_toggler").val();
      $(eo.target).val(current_button_text == 'Expand' ? "Collapse" : "Expand");
  }

  var newid = 0;
  $(".content > pre > code").parent().wrap(function() {
      newid = newid+1;
      return "<div class='code_sample' id='code_autoid_"+newid+"'>";
  });

  var code_samples = $('.code_sample');
  code_samples.find("code").each(function() {
    let jqThis = $(this);
    if (has_scrollbars(this)) {
      jqThis.dblclick(toggle_cs);
      jqThis.attr('title', 'Double-click to expand/collapse');
      var newbtn = $("<input type='button' class='code_toggler' value='Expand' />");
      newbtn.appendTo(jqThis.parents(".code_sample"));
    }
  });

  $(".code_toggler").click(toggle_cs);

  /* fix expand/collapse and tab click hierarchy */
  code_samples.css("position","relative");
  $(".multicode .code_sample").css("position","static");
}


// Code Tabs -------------------------------------------------------------------
// Minitabs adapted from https://code.google.com/p/minitabs/
// Changes made: support multiple tab booklets in one page
/*
The MIT License (MIT)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
*/

jQuery.fn.minitabs = function(speed,effect) {
  this.each(function() {
      var id = "#" + $(this).attr('id')
      $(id + ">DIV:gt(0)").hide();
      $(id + ">UL>LI>A:first").addClass("current");
      $(id + ">UL>LI>A").click(
        function(){
          $(id + ">UL>LI>A").removeClass("current");
          $(this).addClass("current");
          $(this).blur();
          var re = /([_\-\w]+$)/i;
          var target = $('#' + re.exec(this.href)[1]);
          var old = $(id + ">DIV");
          switch (effect) {
            case 'fade':
              old.fadeOut(speed).fadeOut(speed);
              target.fadeIn(speed);
              break;
            case 'slide':
              old.slideUp(speed);
              target.fadeOut(speed).fadeIn(speed);
              break;
            default :
              old.hide(speed);
              target.show(speed)
          }
          return false;
        }
     );
 });
}
