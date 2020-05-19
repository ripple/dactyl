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
