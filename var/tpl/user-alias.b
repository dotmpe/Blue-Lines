comment("""Create or edit? Alias HTML form used on UserPage.
"""),
# TODO: create new alias
div(id="user-alias-actions")
[
  form(id='user-alias-form', action="/~/.action", method="GET")
  [
    fieldset[
        legend['Create/Find Application'],
        input(_id="user-alias-get-or-create", 
            _name="user-alias-get-or-create", 
            value='new-alias ...'),
    ],
    #fieldset[
    #    legend['Delete Application'],
    #    input(_id="user-alias-delete", _name="delete-alias", 
    #        value='alias ...'),
    #],
  ],
  inlineJS("""
      ((function($){

          /* User Alias actions form */
          $(document).ready(function(){
            console.log('doc-ready -:> form-init');
            var frm=$('form#user-alias-form');
            var dflt={};
            $('input', frm).each(function(){
                var nm=$(this).attr('name');
                dflt[nm]=$(this).attr('value'); });
            $('input', frm).bind({
                focus:function(){
                    var nm=$(this).attr('name');
                    var v=$(this).val();
                    if(v==dflt[nm]){$(this).val('')}; },
                blur:function(){
                    var nm=$(this).attr('name');
                    var v=$(this).val();
                    if(v.trim()==''){$(this).val(dflt[nm])}; },
                keypress:function(evt){
                    if (evt.keyCode==13){
                        evt.preventDefault();
                        console.log(evt.keyCode);
                        frm.submit(); }; },
            });
            $(frm).submit(function(evt){
                $('input', frm).each(function(){
                    if($(this).val()==dflt[$(this).attr('name')])
                        $(this).val('');
                });
            });
          });

      })(jQuery));
  """)
]
# vim:et:ts=2:sw=2:ft=python:

