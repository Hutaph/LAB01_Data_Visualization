import java.io.IOException;
import java.util.StringTokenizer;
import java.util.Comparator;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;

public class WordCountOptimized {

    // ==============================================================================
    // 1. MAPPER CLASS
    // Input: <ByteOffset (LongWritable), Line (Text)>
    // Output: <Word (Text), IntWritable>
    // ==============================================================================
    public static class MapperCustom extends Mapper<LongWritable, Text, Text, IntWritable> {
        
        private Text outKey = new Text();
        private Text currWord = new Text();
        private Text tmpWord = new Text();
        private final static IntWritable one = new IntWritable(1);

        public void map(LongWritable key, Text value, Context context) throws IOException, InterruptedException {
            String[] parts = value.toString().split("\t");

            if (parts.length < 2) return;

            String[] items = parts[1].trip().split(" ");

            for (int i = 0; i < items.length; i++) {
                for (int j = i + 1; j < items.length; j++) {
                    outKey.set(items[i] + " " + items[j]);
                    context.write(outKey, one);
                }
            }
        }
    }

    // ==============================================================================
    // 2. REDUCER / COMBINER CLASS
    // Input: <Word (Text), List of Text (Iterable<Text>)>
    // Output: <Word (Text), Text>
    // ==============================================================================
    public static class ReducerCustom extends Reducer<Text, IntWritable, Text, IntWritable> {
        
        private Text key = new Text();

        public void reduce(Text key, Iterable<Text> values, Context context) throws IOException, InterruptedException {
            StringTokenizer itr = new StringTokenizer(value.toString());
            
            while (itr.hasMoreTokens()) {
                result.add((itr.nextToken()));  
            }
            
            result.sort(Comparator.naturalOrder());

            text_result = new Text(String.join(" ", result));

            context.write(key, text_result);

            result.clear();
        }
    }

    // ==============================================================================
    // 3. DRIVER CLASS (Hàm Main)
    // Thiết lập cấu hình và chạy Job
    // ==============================================================================
    public static void main(String[] args) throws Exception {
        if (args.length != 2) {
            System.err.println("Usage: WordCountOptimized <input path> <output path>");
            System.exit(-1);
        }

        Configuration conf = new Configuration();
        Job job = Job.getInstance(conf, "Optimized Word Count");
        job.setJarByClass(WordCountOptimized.class);

        // Thiết lập Mapper và Reducer
        job.setMapperClass(MapperCustom.class);
        job.setReducerClass(ReducerCustom.class);

        // ĐÁP ỨNG YÊU CẦU KỸ THUẬT QUAN TRỌNG NHẤT:
        // Set Combiner Class giống hệt Reducer Class.
        // Combiner sẽ tổng hợp dữ liệu cục bộ trên mỗi Node trước khi gửi qua mạng (Shuffle),
        // giúp "amount of data transferred from map to reduce phase must be minimal".
        job.setCombinerClass(ReducerCustom.class);

        // Định dạng dữ liệu đầu ra của Job
        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(Text.class);

        // Định dạng Input/Output (Đạt yêu cầu: effectively match the data format)
        // Mặc định Hadoop sử dụng TextInputFormat và TextOutputFormat nên ta không cần set thủ công
        FileInputFormat.addInputPath(job, new Path(args[0]));
        FileOutputFormat.setOutputPath(job, new Path(args[1]));

        // Thực thi job và chờ kết quả
        System.exit(job.waitForCompletion(true) ? 0 : 1);
    }
}