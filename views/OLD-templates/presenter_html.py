

header = '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta http-equiv="Content-type" content="text/html; charset=utf-8" />
  <title>Presentation Manager</title>
  <script src="/js/jquery-1.11.2.min.js"></script>
  <!--<script src="/js/sorttable.js"></script>-->
  
  
 <!-- <script src="/js/jquery-1.11.2.min.js"></script>-->
  <link rel="stylesheet" href="/css/style.css" type="text/css" media="all" />


</head>
<body>
<!-- Header -->
<div id="header">
  <div class="shell">
    <!-- Logo + Top Nav -->
    <div id="top">
      <h1><a href="/default">Conference Media Manager</a></h1>
      <div id="top-navigation">
        
        Welcome <strong>firstname| Account type: {type}</strong>
        <span>|</span>
        <a href="http://www.google.com/?gws_rd=ssl#q=help">Help</a>
        <span>|</span>
        <a href="/logout">Log out</a>
          
          <span>|</span>
          <a href="/default">Home</a>
          
        
        
      </div>
    </div>

    </div>
</div>
<!-- End Header -->

<!-- Container -->
<div id="container" >
  <div class="shell"> 
       
    <div id = "warning">
    <div class="msg msg-error">
      <p><strong>Upload in progress do not navigate away from this page</strong></p>
    </div>
    </div>
    <!-- End Message Error -->

    <br />

    <!-- Main -->
    <div id="main">
    <div class="cl">&nbsp;</div>
        <!-- Content -->
        <div id="content">
          
          <!-- Box -->
          <div class="box">

            <!-- Box Head -->
            <div class="box-head">
              <h2 class="left">firstname's Presentations</h2>
            </div>
            <!-- End Box Head --> 
             
            <!-- Table -->
            <div class="presentation-table">
              <table width="100%" border="0" cellspacing="0" cellpadding="0">
                
                <tr>
                  <th width="450px">Session Name</th>
                  <th width = "80px" class="ac">Session Date</th>
                  <th width = "100px" class="ac">Filename</th>
                  <th width ="40px" class="ac">View Presentation</th>
                  <th width ="40px" class="ac">Delete Presentation</th>
                  <th width ="150px" class="ac">Upload Presentation</th>
                  <th></th>
               
                </tr>'''

entries = """                <script>$(document).ready(function(){$('#loading-icon').hide();$('#warning').hide();$('#button{i}').click(function(){$('#loading-icon{i}').show();$('#upload-icon{i}').hide();$('#warning').show();});});</script>
                <tr height = "75px">
                  <td>{session_name}</td>
                  <td>{date_time}</td>
                   {% if filename %}
                  <td class="ac">{filename}</td>
                    {% else %}
                    <td class="ac">--</td>
                  </td>
                {% endif %}
                <!-- Link to current presentation if it exists -->
                {% if blob_store_key == None %}
                    <td class="ac">--</td>
                {% else %}
                  <td class="ac" >
                    <a href = "/serve/blob_store_key.key()}"><img src = "/img/open-file-icon.png" width="20" height ="20" alt = "Open file"></a>
                  
                  </td>
                {% endif %}
                <!--****************************-->
                <!-- Delete presentation -->
                {% blob_store_key == None %}
                    <td class="ac">--</td>
                {% else %}
                    <td class="ac">
                      <form action="{'/delete/%s' % blob_store_key}" method="POST">
                        <input type="hidden" name="session_key" value="{key}">
                        <input type="image" src="/img/delete-icon.png" name="submit" alt="Submit" width="20" height="20"/>
                      </form>
                    </td>
                {% endif %}
                <!--****************************-->
                <!-- Upload presentation -->
                 <td class="ac">
                      <form action="{upload_url}" method="POST" enctype="multipart/form-data">
                        <input type="hidden" name="session_key" value="{key}">
                        <input type="hidden" name="blob_store_key" value="{blob_store_key}">
                        <input type="file" name="file" class = "button" value="upload file"/>

                 </td>
                 <td class="ac">       
                        <div id = "upload-icon"><input type="image" src="/img/upload-icon.png" id="button{i}" name="submit" alt="Submit" width="20" height="20"/></div>
                        <div id = "loading-icon"><img src="/img/small-loading.gif" width="20" height="20"/></div>
                      </form>
                </td>
                
                </tr>"""

footer = """

</table>

                </div>
                </div>
              <!-- End content -->
              <div class="cl">&nbsp;</div>      
              </div>
          <!-- Main -->
            </div>
             <!-- End Shell -->
          </div>

        <!-- End Container -->
      

 <!-- Footer -->
<div id="footer">
  <div class="footer-shell">
    <span class="left">&copy; 2015 - Steven and Jill Marr</span>
    <span class="right">
      Powered by <a href="https://cloud.google.com/appengine/" title="Google App Engine">Google App Engine</a>
    </span>
  </div>
</div>
<!-- End Footer -->
  
</body>
</html>"""
             